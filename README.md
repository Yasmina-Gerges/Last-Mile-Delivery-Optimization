# Last-Mile Delivery Optimization

Simulation and optimization framework for last-mile delivery using AnyLogic, Python and OR-Tools.



## Project Overview

This project combines agent-based simulation and mathematical optimization to improve last-mile delivery operations.

The system models:

- Drivers
- Restaurants
- Customers
- Dynamic traffic conditions
- Stochastic customer demand

Optimization decisions are generated using Mixed Integer Linear Programming (MILP) through OR-Tools, compared against a greedy "nearest rider" baseline.



## Repository Structure

| File | Purpose |
|------|---------|
| `optimizer.py` | Python MILP solver using OR-Tools |
| `requirements.txt` | Python dependencies |
| `presentation.pdf` | Project presentation with simulation screenshots |



## Key Results

| Metric | Improvement |
|--------|-------------|
| Delivery costs | **9% reduction** |
| Average delivery time | **1.9 minutes faster** |

Outperformed nearest-rider dispatching under varying traffic and demand conditions.



## Technologies

- Python (OR-Tools, Flask)
- Java (AnyLogic API)
- AnyLogic (Agent-based simulation)



## How to Run

1. Clone this repository
2. Install dependencies:
3. Run the optimizer:
4. Launch the AnyLogic simulation (requires AnyLogic license)



## Skills Demonstrated

- Operations Research
- Simulation Modeling
- Mathematical Optimization (MILP)
- Supply Chain Analytics
- Python Development



## License

MIT License



## Author

**Yasmina Gerges**  
Industrial Engineering, Lebanese American University (GPA 3.65, Dean's Distinguished List)  
yasmina.gerges@lau.edu | www.linkedin.com/in/yasmina-gerges
