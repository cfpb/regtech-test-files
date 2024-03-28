import random
import string
from typing import List,Iterable

from mock_data.backends import AbstractBackendInterface
from mock_data.backends.Correlation import Correlation

class UniqueID(AbstractBackendInterface):
    def __init__(
        self,
        max_generate: int,
        lei_first: int = 4, 
        lei_middle: int = 14,
        lei_last: int = 2,
        correlation: str = Correlation.INDEPENDENT.name,
        **distribution_kwargs,
    ) -> None:
        """This will create an LEI with a random number of of digits following it as per FIG guidelines. """
        super().__init__(correlation)
        self.lei_first = lei_first
        self.lei_middle = lei_middle
        self.lei_last = lei_last
        self.max_generate = max_generate
    
    def generate_samples(self, size: int, directive: List = None) -> Iterable:
        lei_ids = []
        for i in range(size):
            n = random.randint(1,self.max_generate)
            first = ''.join(random.choices(string.digits, k=self.lei_first))
            middle = ''.join(random.choices(string.ascii_uppercase + string.digits,k=self.lei_middle))
            last = ''.join(random.choices(string.digits,k=self.lei_last))
            final = ''.join(random.choices(string.digits, k=n))
            lei_ids.append(''.join(first+middle+last+final))
        return lei_ids
    

        


    


        
        


