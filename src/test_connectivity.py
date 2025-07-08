"""Test Cloud Run connectivity to various ports."""
import socket
import time
from typing import Dict, Any
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
        "tests": []
    }
    
    for host, port, description in tests:
        logger.info(f"Testing {description} - {host}:{port}")
        test_result = test_port_connectivity(host, port)
        test_result["description"] = description
        results["tests"].append(test_result)
        
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