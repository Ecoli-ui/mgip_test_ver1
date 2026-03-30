from pymgipsim.main import run_simulator_cli
from pymgipsim.Interface.parser import generate_parser_cli
import matplotlib.pyplot as plt

""" Parse Arguments  """
args = generate_parser_cli().parse_args()

run_simulator_cli(args)

plt.show()