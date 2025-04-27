from neo4j import GraphDatabase
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

class Neo4jConnector:
    def __init__(self, uri, username, password):
        """Initialize the Neo4j connector with connection details."""
        self.uri = uri
        self.username = username
        self.password = password
        self.driver = None
        self.logger = logging.getLogger("Neo4jConnector")
        
    def connect(self):
        """Establish a connection to the Neo4j database."""
        try:
            self.driver = GraphDatabase.driver(self.uri, auth=(self.username, self.password))
            # Verify connection
            with self.driver.session() as session:
                result = session.run("RETURN 1")
                for record in result:
                    if record[0] == 1:
                        self.logger.info("Connected to Neo4j database")
                        return True
            return False
        except Exception as e:
            self.logger.error(f"Failed to connect to Neo4j: {e}")
            return False
        
    def query(self, cypher_query, parameters=None):
        """Execute a Cypher query against the Neo4j database and return the results"""
        with self.driver.session() as session:
            result = session.run(cypher_query, parameters or {})
            return [record for record in result] 
           
    def close(self):
        """Close the connection to the Neo4j database."""
        if self.driver:
            self.driver.close()
            self.logger.info("Connection to Neo4j closed")
            self.driver = None
    
    def run_query(self, query, params=None):
        """Run a Cypher query against the Neo4j database."""
        if not self.driver:
            if not self.connect():
                self.logger.error("No connection to database")
                return []
        
        with self.driver.session() as session:
            try:
                result = session.run(query, params or {})
                return [record.data() for record in result]
            except Exception as e:
                self.logger.error(f"Query failed: {e}")
                return []
    
    def get_entity_info(self, entity_name):
        """Get information about a specific entity from the knowledge graph."""
        query = """
        MATCH (n)
        WHERE toLower(n.name) CONTAINS toLower($name)
        RETURN n
        LIMIT 10
        """
        return self.run_query(query, {"name": entity_name})
    
    def get_relationships(self, entity_name):
        """Get relationships for a specific entity from the knowledge graph."""
        query = """
        MATCH (n)-[r]-(m)
        WHERE toLower(n.name) CONTAINS toLower($name) OR 
            (n.title IS NOT NULL AND toLower(n.title) CONTAINS toLower($name))
        RETURN n, type(r) as relationship, m
        LIMIT 20
        """
        return self.run_query(query, {"name": entity_name})

    def search_by_keyword(self, keyword):
        """Search entities by keyword across different properties."""
        query = """
        MATCH (n)
        WHERE ANY(prop IN keys(n) WHERE 
                 toString(n[prop]) IS NOT NULL AND
                 toLower(toString(n[prop])) CONTAINS toLower($keyword))
        RETURN n
        LIMIT 20
        """
        return self.run_query(query, {"keyword": keyword})

def get_knowledge_graph_connector():
    """Create and return a connector to the knowledge graph."""
    # Using the bolt protocol instead of HTTP
    uri = "bolt://123.56.94.39:7687"
    username = "neo4j"
    password = "neo4j2202"
    
    connector = Neo4jConnector(uri, username, password)
    if connector.connect():
        return connector
    else:
        raise ConnectionError("Failed to connect to the Neo4j knowledge graph")

# Example usage
if __name__ == "__main__":
    try:
        kg = get_knowledge_graph_connector()
        print("Successfully connected to Neo4j knowledge graph")
        
        # Example: search for entities related to "museum"
        results = kg.search_by_keyword("克利夫兰博物馆")
        print(f"Found {len(results)} entities related to 'museum'")
        for i, result in enumerate(results[:3], 1):
            print(f"  {i}. {result['n']}")
        
        entity_name = "克利夫兰博物馆"
            
        # relationships = kg.get_relationships(entity_name)
        # print(f"Relationships for '{entity_name}':")
        # for rel in relationships:
        #     print(f"  {rel['n']} - {rel['relationship']} - {rel['m']}")
        
        info = kg.get_entity_info(entity_name)
        print(f"Information for '{entity_name}':")
        for i, info in enumerate(info[:3], 1):
            print(f"  {i}. {info['n']}")
        
        kg.close()
    except Exception as e:
        print(f"Error: {e}")