"""Test Cloud Run connectivity to various ports."""
import socket
import time
import ssl
import subprocess
from typing import Dict, Any, Optional
from urllib.parse import urlparse
import structlog

logger = structlog.get_logger()


def test_port_connectivity(host: str, port: int, timeout: int = 5) -> Dict[str, Any]:
    """Test TCP connectivity to a host:port combination."""
    start_time = time.time()
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    
    result = {
        "host": host,
        "port": port,
        "success": False,
        "error": None,
        "response_time": None,
        "resolved_ip": None
    }
    
    try:
        # Resolve hostname
        ip_address = socket.gethostbyname(host)
        result["resolved_ip"] = ip_address
        logger.info(f"Resolved {host} to {ip_address}")
        
        # Try to connect
        sock.connect((ip_address, port))
        result["success"] = True
        result["response_time"] = time.time() - start_time
        logger.info(f"Successfully connected to {host}:{port}")
        
    except socket.gaierror as e:
        result["error"] = f"DNS resolution failed: {str(e)}"
        logger.error(f"DNS resolution failed for {host}: {str(e)}")
        
    except socket.timeout:
        result["error"] = f"Connection timed out after {timeout}s"
        logger.error(f"Connection timed out to {host}:{port}")
        
    except Exception as e:
        result["error"] = f"Connection failed: {str(e)}"
        logger.error(f"Connection failed to {host}:{port}: {str(e)}")
        
    finally:
        sock.close()
        
    return result


def test_ssl_certificate(host: str, port: int = 443) -> Dict[str, Any]:
    """Test SSL certificate details for a host."""
    result = {
        "host": host,
        "port": port,
        "ssl_verified": False,
        "certificate_info": None,
        "error": None
    }
    
    try:
        # Create SSL context
        context = ssl.create_default_context()
        
        # Connect and get certificate
        with socket.create_connection((host, port), timeout=10) as sock:
            with context.wrap_socket(sock, server_hostname=host) as ssock:
                cert = ssock.getpeercert()
                result["ssl_verified"] = True
                result["certificate_info"] = {
                    "subject": dict(x[0] for x in cert.get('subject', [])),
                    "issuer": dict(x[0] for x in cert.get('issuer', [])),
                    "version": cert.get('version'),
                    "serial_number": cert.get('serialNumber'),
                    "not_before": cert.get('notBefore'),
                    "not_after": cert.get('notAfter'),
                    "san": cert.get('subjectAltName', [])
                }
                result["protocol"] = ssock.version()
                result["cipher"] = ssock.cipher()
                
    except Exception as e:
        result["error"] = f"SSL test failed: {str(e)}"
        logger.error(f"SSL certificate test failed for {host}:{port}", error=str(e))
        
    return result


def test_neo4j_specific_diagnostics(neo4j_uri: Optional[str] = None) -> Dict[str, Any]:
    """Comprehensive Neo4j connectivity diagnostics."""
    # Get Neo4j URI from config if not provided
    if not neo4j_uri:
        try:
            from .config_wrapper import Config
            config = Config()
            neo4j_uri = config.NEO4J_URI
        except Exception as e:
            return {"error": f"Failed to load Neo4j config: {str(e)}"}
    
    # Parse URI
    parsed = urlparse(neo4j_uri)
    host = parsed.hostname
    port = parsed.port or 7687
    scheme = parsed.scheme
    
    diagnostics = {
        "uri_info": {
            "original_uri": neo4j_uri,
            "scheme": scheme,
            "hostname": host,
            "port": port,
            "is_encrypted": scheme in ['neo4j+s', 'bolt+s', 'neo4j+ssc', 'bolt+ssc']
        },
        "tests": {}
    }
    
    logger.info(f"Starting Neo4j diagnostics for {host}:{port}")
    
    # 1. DNS Resolution Test
    try:
        dns_start = time.time()
        resolved_addresses = socket.getaddrinfo(host, port, socket.AF_UNSPEC, socket.SOCK_STREAM)
        dns_time = time.time() - dns_start
        
        diagnostics["tests"]["dns_resolution"] = {
            "success": True,
            "resolution_time_ms": f"{dns_time * 1000:.1f}",
            "addresses": [
                {
                    "family": "IPv6" if addr[0] == socket.AF_INET6 else "IPv4",
                    "ip": addr[4][0],
                    "port": addr[4][1]
                } for addr in resolved_addresses
            ],
            "address_count": len(resolved_addresses)
        }
    except Exception as e:
        diagnostics["tests"]["dns_resolution"] = {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__
        }
    
    # 2. TCP Connectivity Test
    if diagnostics["tests"]["dns_resolution"]["success"]:
        primary_ip = diagnostics["tests"]["dns_resolution"]["addresses"][0]["ip"]
        
        try:
            tcp_start = time.time()
            test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            test_socket.settimeout(15)
            test_socket.connect((primary_ip, port))
            tcp_time = time.time() - tcp_start
            test_socket.close()
            
            diagnostics["tests"]["tcp_connectivity"] = {
                "success": True,
                "target_ip": primary_ip,
                "connect_time_ms": f"{tcp_time * 1000:.1f}"
            }
        except Exception as e:
            diagnostics["tests"]["tcp_connectivity"] = {
                "success": False,
                "target_ip": primary_ip,
                "error": str(e),
                "error_type": type(e).__name__
            }
    
    # 3. SSL Certificate Test (if encrypted connection)
    if diagnostics["uri_info"]["is_encrypted"]:
        try:
            ssl_result = test_ssl_certificate(host, port)
            diagnostics["tests"]["ssl_certificate"] = ssl_result
        except Exception as e:
            diagnostics["tests"]["ssl_certificate"] = {
                "error": f"SSL test failed: {str(e)}"
            }
    
    # 4. Network Path Analysis (ping test)
    try:
        ping_result = subprocess.run(
            ["ping", "-c", "4", "-W", "3000", host],
            capture_output=True,
            text=True,
            timeout=15
        )
        
        if ping_result.returncode == 0:
            # Parse ping output for latency info
            lines = ping_result.stdout.strip().split('\n')
            stats_line = [line for line in lines if 'min/avg/max' in line]
            
            diagnostics["tests"]["ping"] = {
                "success": True,
                "stats": stats_line[0] if stats_line else "No stats found",
                "packet_count": 4
            }
        else:
            diagnostics["tests"]["ping"] = {
                "success": False,
                "error": ping_result.stderr or "Ping failed"
            }
    except Exception as e:
        diagnostics["tests"]["ping"] = {
            "success": False,
            "error": f"Ping test failed: {str(e)}"
        }
    
    # 5. MTU Discovery Test
    try:
        mtu_sizes = [576, 1000, 1460, 1500]
        mtu_results = []
        
        for size in mtu_sizes:
            try:
                mtu_result = subprocess.run(
                    ["ping", "-c", "1", "-s", str(size), "-M", "do", host],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                mtu_results.append({
                    "packet_size": size,
                    "success": mtu_result.returncode == 0,
                    "fragmentation_needed": "frag needed" in mtu_result.stderr.lower()
                })
            except:
                mtu_results.append({
                    "packet_size": size,
                    "success": False,
                    "error": "Test timeout or failure"
                })
        
        diagnostics["tests"]["mtu_discovery"] = mtu_results
    except Exception as e:
        diagnostics["tests"]["mtu_discovery"] = {"error": str(e)}
    
    # 6. Traceroute (simplified)
    try:
        traceroute_result = subprocess.run(
            ["traceroute", "-m", "10", "-w", "2", host],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if traceroute_result.returncode == 0:
            # Count the number of hops
            hops = len([line for line in traceroute_result.stdout.split('\n') if line.strip() and not line.startswith('traceroute')])
            diagnostics["tests"]["traceroute"] = {
                "success": True,
                "hop_count": hops,
                "max_hops_tested": 10
            }
        else:
            diagnostics["tests"]["traceroute"] = {
                "success": False,
                "error": "Traceroute failed or timed out"
            }
    except Exception as e:
        diagnostics["tests"]["traceroute"] = {
            "success": False,
            "error": f"Traceroute test failed: {str(e)}"
        }
    
    return diagnostics


def run_connectivity_tests() -> Dict[str, Any]:
    """Run connectivity tests to various services and ports."""
    tests = [
        # Standard web ports (should work)
        ("google.com", 80, "HTTP"),
        ("google.com", 443, "HTTPS"),
        
        # Neo4j Aura
        ("ab2b5664.databases.neo4j.io", 7687, "Neo4j Bolt"),
        ("ab2b5664.databases.neo4j.io", 443, "Neo4j HTTPS"),
        
        # Other databases for comparison
        ("smtp.gmail.com", 587, "SMTP"),
        ("1.1.1.1", 53, "DNS"),
        
        # MongoDB Atlas (another cloud database)
        ("cluster0.mongodb.net", 27017, "MongoDB"),
        
        # PostgreSQL (common port)
        ("8.8.8.8", 5432, "PostgreSQL test"),
    ]
    
    results = {
        "timestamp": time.time(),
        "basic_connectivity_tests": [],
        "neo4j_detailed_diagnostics": None
    }
    
    # Run basic connectivity tests
    for host, port, description in tests:
        logger.info(f"Testing {description} - {host}:{port}")
        test_result = test_port_connectivity(host, port)
        test_result["description"] = description
        results["basic_connectivity_tests"].append(test_result)
    
    # Run comprehensive Neo4j diagnostics
    logger.info("Running detailed Neo4j diagnostics")
    results["neo4j_detailed_diagnostics"] = test_neo4j_specific_diagnostics()
        
    return results


if __name__ == "__main__":
    # Run tests
    results = run_connectivity_tests()
    
    # Print summary
    print("\n=== Connectivity Test Results ===")
    for test in results["tests"]:
        status = "✓" if test["success"] else "✗"
        print(f"{status} {test['description']} ({test['host']}:{test['port']})")
        if test["resolved_ip"]:
            print(f"   Resolved to: {test['resolved_ip']}")
        if test["error"]:
            print(f"   Error: {test['error']}")
        if test["response_time"]:
            print(f"   Response time: {test['response_time']:.3f}s")
        print()