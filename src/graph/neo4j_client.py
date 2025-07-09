"""Neo4j database client and operations."""
from typing import List, Dict, Any, Optional, Callable
from urllib.parse import urlparse
from neo4j import GraphDatabase
import structlog
from datetime import datetime
import socket
import ssl
import time
import random
from functools import wraps
from ..models.newsletter import Entity, Newsletter
from ..config_wrapper import Config

logger = structlog.get_logger()


def retry_with_exponential_backoff(max_retries: int = 3, initial_delay: float = 1.0, 
                                  max_delay: float = 60.0, exponential_base: float = 2.0,
                                  jitter: bool = True) -> Callable:
    """
    Decorator that implements exponential backoff retry logic.
    
    Args:
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay in seconds
        max_delay: Maximum delay in seconds
        exponential_base: Base for exponential calculation
        jitter: Whether to add randomness to delay
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            attempt = 0
            delay = initial_delay
            
            while attempt <= max_retries:
                try:
                    if attempt > 0:
                        logger.info(f"Retry attempt {attempt} for {func.__name__}",
                                   attempt=attempt,
                                   max_retries=max_retries,
                                   delay_used=f"{delay:.2f}s")
                    
                    result = func(*args, **kwargs)
                    
                    if attempt > 0:
                        logger.info(f"Retry successful for {func.__name__}",
                                   successful_attempt=attempt + 1,
                                   total_attempts=attempt + 1)
                    
                    return result
                    
                except Exception as e:
                    attempt += 1
                    
                    logger.warning(f"Attempt {attempt} failed for {func.__name__}",
                                 error_type=type(e).__name__,
                                 error_message=str(e),
                                 attempt=attempt,
                                 max_retries=max_retries)
                    
                    if attempt > max_retries:
                        logger.error(f"All retry attempts exhausted for {func.__name__}",
                                   total_attempts=attempt,
                                   final_error=str(e))
                        raise
                    
                    # Calculate delay with exponential backoff
                    delay = min(delay * exponential_base, max_delay)
                    
                    # Add jitter to prevent thundering herd
                    if jitter:
                        jitter_delay = delay * (0.5 + random.random() * 0.5)
                    else:
                        jitter_delay = delay
                    
                    logger.info(f"Waiting before retry for {func.__name__}",
                              base_delay=f"{delay:.2f}s",
                              actual_delay=f"{jitter_delay:.2f}s",
                              next_attempt=attempt + 1)
                    
                    time.sleep(jitter_delay)
            
            raise Exception(f"Unexpected error in retry logic for {func.__name__}")
        
        return wrapper
    return decorator


class Neo4jClient:
    """Neo4j database client for graph operations."""
    
    def __init__(self, config: Config):
        self.config = config
        self.driver = None
        self.connection_attempts = 0
        self.last_connection_error = None
    
    @retry_with_exponential_backoff(max_retries=3, initial_delay=2.0, max_delay=30.0)
    def _create_neo4j_driver(self) -> GraphDatabase.driver:
        """Create Neo4j driver with retry logic and extended timeouts."""
        # Extended timeouts for Cloud Run environment
        connection_timeout = getattr(self.config, 'NEO4J_CONNECTION_TIMEOUT', 120)
        acquisition_timeout = getattr(self.config, 'NEO4J_ACQUISITION_TIMEOUT', 90)
        
        logger.info("Creating Neo4j driver with extended timeouts",
                   connection_timeout=connection_timeout,
                   acquisition_timeout=acquisition_timeout)
        
        return GraphDatabase.driver(
            self.config.NEO4J_URI, 
            auth=(self.config.NEO4J_USER, self.config.NEO4J_PASSWORD),
            max_connection_lifetime=3600,
            max_connection_pool_size=50,
            connection_acquisition_timeout=acquisition_timeout,
            connection_timeout=connection_timeout,
            keep_alive=True,
            resolver=None,  # Use default resolver
            encrypted=None,  # Auto-detect from URI
            trust=None,      # Default trust settings
            user_agent="arrgh-fastapi/1.0 (Cloud Run)"
        )
    
    @retry_with_exponential_backoff(max_retries=2, initial_delay=1.0, max_delay=15.0)
    def _test_connection(self) -> dict:
        """Test the connection with a simple query."""
        with self.driver.session(database=self.config.NEO4J_DATABASE) as session:
            result = session.run("RETURN 1 as test, datetime() as server_time")
            return result.single()
        
    def connect(self) -> bool:
        """Establish connection to Neo4j with comprehensive logging."""
        start_time = time.time()
        
        try:
            # Parse and log connection details (without password)
            parsed_uri = urlparse(self.config.NEO4J_URI)
            sanitized_uri = f"{parsed_uri.scheme}://{parsed_uri.hostname}:{parsed_uri.port}"
            
            logger.info("Starting Neo4j connection attempt", 
                       uri=sanitized_uri,
                       user=self.config.NEO4J_USER,
                       password_length=len(self.config.NEO4J_PASSWORD) if self.config.NEO4J_PASSWORD else 0,
                       scheme=parsed_uri.scheme,
                       hostname=parsed_uri.hostname,
                       port=parsed_uri.port or 7687)
            
            # DNS Resolution with timing
            dns_start = time.time()
            try:
                resolved_addresses = socket.getaddrinfo(
                    parsed_uri.hostname, 
                    parsed_uri.port or 7687,
                    socket.AF_UNSPEC,
                    socket.SOCK_STREAM
                )
                dns_time = time.time() - dns_start
                
                ip_addresses = [addr[4][0] for addr in resolved_addresses]
                logger.info("DNS resolution successful",
                           hostname=parsed_uri.hostname,
                           resolved_ips=ip_addresses,
                           dns_resolution_time_ms=f"{dns_time * 1000:.1f}",
                           address_count=len(resolved_addresses))
                
                # Log address family info
                for addr in resolved_addresses:
                    family_name = "IPv6" if addr[0] == socket.AF_INET6 else "IPv4"
                    logger.debug("Resolved address details",
                               family=family_name,
                               ip=addr[4][0],
                               port=addr[4][1])
                               
            except socket.gaierror as e:
                dns_time = time.time() - dns_start
                logger.error("DNS resolution failed",
                            hostname=parsed_uri.hostname,
                            error=str(e),
                            error_code=e.errno,
                            dns_attempt_time_ms=f"{dns_time * 1000:.1f}")
                return False
            
            # SSL/TLS information
            is_encrypted = parsed_uri.scheme in ['neo4j+s', 'bolt+s', 'neo4j+ssc', 'bolt+ssc']
            logger.info("Connection encryption details",
                       is_encrypted=is_encrypted,
                       scheme=parsed_uri.scheme,
                       expects_ssl=is_encrypted)
            
            # Test basic TCP connectivity first
            tcp_start = time.time()
            try:
                test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                connection_timeout = getattr(self.config, 'NEO4J_CONNECTION_TIMEOUT', 120)
                test_socket.settimeout(connection_timeout)
                test_socket.connect((ip_addresses[0], parsed_uri.port or 7687))
                tcp_time = time.time() - tcp_start
                test_socket.close()
                
                logger.info("TCP connectivity test successful",
                           ip=ip_addresses[0],
                           port=parsed_uri.port or 7687,
                           tcp_connect_time_ms=f"{tcp_time * 1000:.1f}")
                           
            except Exception as e:
                tcp_time = time.time() - tcp_start
                logger.error("TCP connectivity test failed",
                            ip=ip_addresses[0] if ip_addresses else "unknown",
                            port=parsed_uri.port or 7687,
                            error=str(e),
                            tcp_attempt_time_ms=f"{tcp_time * 1000:.1f}")
                return False
            
            # Create Neo4j driver with retry logic
            driver_start = time.time()
            connection_timeout = getattr(self.config, 'NEO4J_CONNECTION_TIMEOUT', 120)
            acquisition_timeout = getattr(self.config, 'NEO4J_ACQUISITION_TIMEOUT', 90)
            logger.info("Creating Neo4j driver with retry logic enabled",
                       max_connection_lifetime=3600,
                       max_connection_pool_size=50,
                       connection_acquisition_timeout=acquisition_timeout,
                       connection_timeout=connection_timeout)
            
            try:
                self.driver = self._create_neo4j_driver()
                driver_time = time.time() - driver_start
                logger.info("Neo4j driver created successfully",
                           driver_creation_time_ms=f"{driver_time * 1000:.1f}")
            except Exception as e:
                driver_time = time.time() - driver_start
                logger.error("Failed to create Neo4j driver after retries",
                            error_type=type(e).__name__,
                            error_message=str(e),
                            driver_attempt_time_ms=f"{driver_time * 1000:.1f}")
                self.last_connection_error = str(e)
                return False
            
            # Test actual Neo4j connection with retry logic
            session_start = time.time()
            try:
                record = self._test_connection()
                session_time = time.time() - session_start
                
                logger.info("Neo4j connection test successful",
                           session_test_time_ms=f"{session_time * 1000:.1f}",
                           test_result=record["test"],
                           server_time=str(record["server_time"]),
                           database=self.config.NEO4J_DATABASE)
                           
            except Exception as e:
                session_time = time.time() - session_start
                logger.error("Neo4j connection test failed after retries",
                            error_type=type(e).__name__,
                            error_message=str(e),
                            session_attempt_time_ms=f"{session_time * 1000:.1f}",
                            database=self.config.NEO4J_DATABASE)
                
                # Log Neo4j-specific error details
                if hasattr(e, 'code'):
                    logger.error("Neo4j error code", code=e.code)
                if hasattr(e, 'classification'):
                    logger.error("Neo4j error classification", classification=e.classification)
                if hasattr(e, 'category'):
                    logger.error("Neo4j error category", category=e.category)
                
                self.last_connection_error = str(e)
                return False
            
            total_time = time.time() - start_time
            logger.info("Neo4j connection established successfully",
                       total_connection_time_ms=f"{total_time * 1000:.1f}",
                       dns_time_ms=f"{dns_time * 1000:.1f}",
                       tcp_time_ms=f"{tcp_time * 1000:.1f}",
                       driver_time_ms=f"{driver_time * 1000:.1f}",
                       session_time_ms=f"{(time.time() - session_start) * 1000:.1f}")
            
            return True
            
        except Exception as e:
            total_time = time.time() - start_time
            logger.error("Neo4j connection failed with unexpected error",
                        error_type=type(e).__name__,
                        error_message=str(e),
                        error_details=repr(e),
                        total_attempt_time_ms=f"{total_time * 1000:.1f}")
            
            self.last_connection_error = str(e)
            self.connection_attempts += 1
            return False
    
    def get_connection_health(self) -> Dict[str, Any]:
        """Get detailed connection health information."""
        health_info = {
            "has_driver": self.driver is not None,
            "connection_attempts": self.connection_attempts,
            "last_error": self.last_connection_error,
            "driver_info": None
        }
        
        if self.driver:
            try:
                # Test if driver is still valid
                test_start = time.time()
                with self.driver.session() as session:
                    result = session.run("RETURN 1")
                    result.single()
                test_time = time.time() - test_start
                
                health_info["driver_info"] = {
                    "is_healthy": True,
                    "test_query_time_ms": f"{test_time * 1000:.1f}",
                    "encrypted": getattr(self.driver, 'encrypted', None)
                }
                
            except Exception as e:
                health_info["driver_info"] = {
                    "is_healthy": False,
                    "error": str(e),
                    "error_type": type(e).__name__
                }
        
        return health_info
    
    def reconnect_if_needed(self) -> bool:
        """Reconnect if the current connection is unhealthy."""
        health = self.get_connection_health()
        
        if not health["has_driver"] or not health.get("driver_info", {}).get("is_healthy", False):
            logger.info("Connection unhealthy, attempting reconnect",
                       connection_attempts=self.connection_attempts,
                       last_error=self.last_connection_error)
            
            # Close existing driver if any
            if self.driver:
                try:
                    self.driver.close()
                except:
                    pass
                self.driver = None
            
            return self.connect()
        
        return True
    
    def close(self):
        """Close Neo4j connection."""
        if self.driver:
            self.driver.close()
            logger.info("Neo4j connection closed")
    
    def execute_query(self, query: str, parameters: dict = None) -> Optional[List[Dict]]:
        """Execute a Cypher query."""
        if not self.driver:
            logger.error("No Neo4j connection")
            return None
        
        try:
            with self.driver.session(database=self.config.NEO4J_DATABASE) as session:
                result = session.run(query, parameters or {})
                return result.data()
        except Exception as e:
            logger.error("Query execution failed", query=query[:100], error=str(e))
            return None
    
    def setup_constraints_and_indexes(self):
        """Create constraints and indexes for optimal graph performance."""
        if not self.driver:
            logger.error("No Neo4j connection available")
            return
        
        constraints_and_indexes = [
            # Unique constraints
            "CREATE CONSTRAINT unique_org_name IF NOT EXISTS FOR (o:Organization) REQUIRE o.name IS UNIQUE",
            "CREATE CONSTRAINT unique_person_name IF NOT EXISTS FOR (p:Person) REQUIRE p.name IS UNIQUE",
            "CREATE CONSTRAINT unique_product_name IF NOT EXISTS FOR (pr:Product) REQUIRE pr.name IS UNIQUE",
            "CREATE CONSTRAINT unique_event_name IF NOT EXISTS FOR (e:Event) REQUIRE e.name IS UNIQUE",
            "CREATE CONSTRAINT unique_location_name IF NOT EXISTS FOR (l:Location) REQUIRE l.name IS UNIQUE",
            "CREATE CONSTRAINT unique_topic_name IF NOT EXISTS FOR (t:Topic) REQUIRE t.name IS UNIQUE",
            "CREATE CONSTRAINT unique_newsletter_id IF NOT EXISTS FOR (n:Newsletter) REQUIRE n.id IS UNIQUE",
            
            # Performance indexes
            "CREATE INDEX newsletter_date_idx IF NOT EXISTS FOR (n:Newsletter) ON (n.received_date)",
            "CREATE INDEX entity_confidence_idx IF NOT EXISTS FOR (e:Organization) ON (e.confidence)",
            "CREATE INDEX entity_last_seen_idx IF NOT EXISTS FOR (e:Organization) ON (e.last_seen)",
        ]
        
        logger.info("Setting up graph constraints and indexes")
        
        for constraint in constraints_and_indexes:
            try:
                self.execute_query(constraint)
                constraint_name = constraint.split()[2]
                logger.info("Constraint/index created", name=constraint_name)
            except Exception as e:
                logger.warning("Constraint/index creation failed", 
                             constraint=constraint.split()[2], 
                             error=str(e))
    
    def create_or_update_entity(self, entity: Entity) -> Optional[Dict]:
        """Create or update an entity node in the graph."""
        # Convert properties to a JSON string if not empty, otherwise set to null
        import json
        properties_json = json.dumps(entity.properties) if entity.properties else None
        
        query = f"""
        MERGE (e:{entity.type} {{name: $name}})
        ON CREATE SET 
            e.created_at = datetime(),
            e.confidence = $confidence,
            e.aliases = $aliases,
            e.mention_count = 1,
            e.properties_json = $properties_json
        ON MATCH SET
            e.last_seen = datetime(),
            e.mention_count = e.mention_count + 1,
            e.confidence = CASE 
                WHEN $confidence > e.confidence THEN $confidence 
                ELSE e.confidence 
            END
        RETURN e, 
               CASE WHEN e.created_at = e.last_seen THEN 'created' ELSE 'updated' END as operation
        """
        
        parameters = {
            'name': entity.name,
            'confidence': entity.confidence,
            'aliases': entity.aliases,
            'properties_json': properties_json
        }
        
        result = self.execute_query(query, parameters)
        return result[0] if result else None
    
    def create_newsletter_node(self, newsletter: Newsletter) -> Optional[Dict]:
        """Create a newsletter node in the graph."""
        query = """
        MERGE (n:Newsletter {id: $newsletter_id})
        ON CREATE SET
            n.subject = $subject,
            n.sender = $sender,
            n.received_date = $received_date,
            n.created_at = datetime(),
            n.content_length = $content_length
        RETURN n
        """
        
        parameters = {
            'newsletter_id': newsletter.newsletter_id,
            'subject': newsletter.subject,
            'sender': newsletter.sender,
            'received_date': newsletter.received_date.isoformat() if newsletter.received_date else None,
            'content_length': len(newsletter.html_content)
        }
        
        result = self.execute_query(query, parameters)
        return result[0] if result else None
    
    def link_entity_to_newsletter(self, entity_name: str, entity_type: str, 
                                 newsletter_id: str, context: str = None) -> Optional[Dict]:
        """Create a MENTIONED_IN relationship between entity and newsletter."""
        query = f"""
        MATCH (e:{entity_type} {{name: $entity_name}})
        MATCH (n:Newsletter {{id: $newsletter_id}})
        MERGE (e)-[r:MENTIONED_IN]->(n)
        ON CREATE SET
            r.date = datetime(),
            r.context = $context
        RETURN r
        """
        
        parameters = {
            'entity_name': entity_name,
            'newsletter_id': newsletter_id,
            'context': context
        }
        
        result = self.execute_query(query, parameters)
        return result[0] if result else None
    
    def find_similar_entities(self, entity_name: str, entity_type: str, 
                            similarity_threshold: float = 0.8) -> List[Dict]:
        """Find entities with similar names for resolution."""
        query = f"""
        MATCH (e:{entity_type})
        WHERE e.name CONTAINS $search_term 
           OR ANY(alias IN e.aliases WHERE alias CONTAINS $search_term)
           OR $search_term CONTAINS e.name
        RETURN e, 
               e.mention_count as popularity,
               e.confidence as confidence
        ORDER BY popularity DESC, confidence DESC
        LIMIT 10
        """
        
        parameters = {'search_term': entity_name}
        result = self.execute_query(query, parameters)
        return result or []
    
    def get_graph_stats(self) -> Dict[str, int]:
        """Get basic statistics about the graph."""
        stats_query = """
        CALL {
            MATCH (o:Organization) RETURN count(o) as organizations
        }
        CALL {
            MATCH (p:Person) RETURN count(p) as people
        }
        CALL {
            MATCH (pr:Product) RETURN count(pr) as products
        }
        CALL {
            MATCH (e:Event) RETURN count(e) as events
        }
        CALL {
            MATCH (l:Location) RETURN count(l) as locations
        }
        CALL {
            MATCH (t:Topic) RETURN count(t) as topics
        }
        CALL {
            MATCH (n:Newsletter) RETURN count(n) as newsletters
        }
        CALL {
            MATCH ()-[r]->() RETURN count(r) as relationships
        }
        RETURN organizations, people, products, events, locations, topics, newsletters, relationships
        """
        
        result = self.execute_query(stats_query)
        return result[0] if result else {}