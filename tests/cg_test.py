import sys
import unittest

sys.path.append('../../')
from krylov.util import loader, toepliz_matrix_generator
from krylov.single.cg import cg
import numpy as np 

class TestCgMethod(unittest.TestCase):
    epsilon = 1e-8
    T = np.float64

    def test_single_cg_method(self):
        A ,b = toepliz_matrix_generator.generate()
        self.assertTrue(cg(A, b, TestCgMethod.epsilon, TestCgMethod.T))

if __name__ == "__main__":
    unittest.main()