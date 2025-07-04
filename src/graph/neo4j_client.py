"""Neo4j database client and operations."""
from typing import List, Dict, Any, Optional
from neo4j import GraphDatabase
import structlog
from datetime import datetime
from ..models.newsletter import Entity, Newsletter
from ..config_wrapper import Config

logger = structlog.get_logger()


class Neo4jClient:
    """Neo4j database client for graph operations."""
    
    def __init__(self, config: Config):
        self.config = config
        self.driver = None
        
    def connect(self) -> bool:
        """Establish connection to Neo4j."""
        try:
            self.driver = GraphDatabase.driver(
                self.config.NEO4J_URI, 
                auth=(self.config.NEO4J_USER, self.config.NEO4J_PASSWORD)
            )
            # Test connection
            with self.driver.session() as session:
                result = session.run("RETURN 1 as test")
                result.single()
            logger.info("Neo4j connection established")
            return True
        except Exception as e:
            logger.error("Neo4j connection failed", error=str(e))
            return False
    
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
        query = f"""
        MERGE (e:{entity.type} {{name: $name}})
        ON CREATE SET 
            e.created_at = datetime(),
            e.confidence = $confidence,
            e.aliases = $aliases,
            e.mention_count = 1,
            e.properties = $properties
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
            'properties': entity.properties
        }
        
        result = self.execute_query(query, parameters)
        return result[0] if result else None
    
    def create_newsletter_node(self, newsletter: Newsletter) -> Optional[Dict]:
        """Create a newsletter node in the graph."""
        query = """
        CREATE (n:Newsletter {
            id: $newsletter_id,
            subject: $subject,
            sender: $sender,
            received_date: $received_date,
            created_at: datetime(),
            content_length: $content_length
        })
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
        CREATE (e)-[r:MENTIONED_IN {{
            date: datetime(),
            context: $context
        }}]->(n)
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