from game.engine import Session
from skls_embeddings.chroma_client import ChromaClient
from skls_generator.generator import Generator

class Magg:
    def __init__(self, instructions_filename, chroma_client : ChromaClient, generator : Generator, game_state : Session) -> None:
        with open(instructions_filename, 'r') as file:
            self.instructions = file.read()
        self.chroma_client = chroma_client
        self.collection_name = "magg_memory"
        self.session = game_state
        self.generator = generator
        
    
    def get_memory(self, request, n_results=5)->list[str]:
        '''
        Retrieve relevant memory entries from the ChromaDB collection based on the request.
        '''
        results = self.chroma_client.search_in_dedicated_collection(self.collection_name, request, n_results)
        return results['documents'] if results['documents'] else [] # type: ignore
    
    