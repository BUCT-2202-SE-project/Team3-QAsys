from neo4j import GraphDatabase

class Neo4jConnection:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def query(self, query, parameters=None):
        with self.driver.session() as session:
            result = session.run(query, parameters)
            return [record for record in result]

# 初始化连接
neo4j_conn = Neo4jConnection(
    uri="bolt://123.56.94.39:7687",
    user="neo4j",
    password=""
)
