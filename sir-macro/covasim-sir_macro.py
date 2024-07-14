from main import *
import numpy as np
import matplotlib.pyplot as plt
from utilities import *
import pandas as pd
from pandas import DataFrame
from math import ceil
import sys
sys.path.insert(0, '..')
from find_policy import *

class sir_macro_obj():
        def __init__(self, medical_dict, start_stayhome, end_stayhome, sim_duraion=150, verbose=False):
                self.medical_dict = medical_dict
                self.start_stayhome = start_stayhome
                self.end_stayhome = end_stayhome
                self.sim_duraion = sim_duraion
                self.verbose = verbose
                self.best_policy = None
                self.policy_history = None
                self.loss_history = None
                self.ss = initial_ss() # pre-pandemic steady state

        def sir_macro(self, ctax_intensity):
                # ss = initial_ss() 
                # # if self.verbose:
                # #         print('Steady state:', ss)
                print("calling sir-macro")
                ctax_policy = np.zeros(self.sim_duraion)
                ctax_policy[self.start_stayhome:self.end_stayhome+1] = ctax_intensity 
                td = td_solve(ctax=ctax_policy, pr_treat=self.medical_dict['treat'], pr_vacc=self.medical_dict['vax'], pi1=0.0046, pi2=7.3983, pi3=0.2055,
                        eps=0.001, pidbar=0.07 / 18, pir=0.99 * 7 / 18, kappa=0.0, phi=0.8, theta=36, A=39.8, beta=0.96**(1/52), maxit=100,
                        h=1E-4, tol=1E-8, noisy=False, H_U=None)
                td = pd.DataFrame(td)
                return td

        def loss_sir_macro(self, ctax_intensity):
                print("calling loss_sir_macro")
                try:
                        td_res = self.sir_macro(ctax_intensity)
                        loss = np.square(td_res['I'] - self.medical_dict['covasim_res']['I']).sum()
                except Exception as e:
                        print("sir-macro error:", e)
                        loss = -1
                return loss

        def find_best_ctax(self, ctax_intensity):
                print("find_best_ctax")
                self.best_policy, self.policy_history, self.loss_history = gradient_descent_with_adam(self.loss_sir_macro, ctax_intensity, learning_rate=1,
                                                         epochs=1, verbose=self.verbose, patience=5, save_policy_as=None)
                return self.best_policy, self.policy_history, self.loss_history

        def visualize(self):
                if self.best_policy == None:
                        raise Exception("No best policy found. Run find_best_ctax() first.")
                td1 = td_solve(ctax=np.full(self.sim_duraion, 0), pr_treat=self.medical_dict['treat'], pr_vacc=self.medical_dict['vax'], pi1=0.0046, pi2=7.3983, pi3=0.2055,
                        eps=0.001, pidbar=0.07 / 18, pir=0.99 * 7 / 18, kappa=0.0, phi=0.8, theta=36, A=39.8, beta=0.96**(1/52), maxit=50,
                        h=1E-4, tol=1E-8, noisy=False, H_U=None)


                ctax_policy = np.zeros(self.sim_duraion)
                ctax_policy[self.start_stayhome:self.end_stayhome+1] = self.best_policy['ctax_intensity'] 

                td2 = td_solve(ctax=ctax_policy, pr_treat=self.medical_dict['treat'], pr_vacc=self.medical_dict['vax'], pi1=0.0046, pi2=7.3983, pi3=0.2055,
                        eps=0.001, pidbar=0.07 / 18, pir=0.99 * 7 / 18, kappa=0.0, phi=0.8, theta=36, A=39.8, beta=0.96**(1/52), maxit=100,
                        h=1E-4, tol=1E-8, noisy=False, H_U=None)

                td1 = pd.DataFrame(td1)
                td2 = pd.DataFrame(td2)

                scenarios = [{'df': td1, 'name': 'No Policy', 'csv_name': './csv/td1.csv'},
                             {'df': td2, 'name': 'Custom Policy', 'csv_name': './csv/td2.csv'},
                             {'df': self.medical_dict['covasim_res'], 'name': 'Covasim', 'csv_name': './csv/td0.csv'}]

                vars = [{"key": "I", "name": "Infected", "y_unit": "% initial pop."},
                        {"key": "S", "name": "Susceptible", "y_unit": "% initial pop."},
                        {"key": "D", "name": "Death", "y_unit": "% initial pop."},
                        {"key": "T", "name": "New Infections", "y_unit": "% initial pop."},
                        {"key": "C", "name": "Aggregate Consumption", "y_unit": ""},
                        {"key": "N", "name": "Aggregate labor supply", "y_unit": ""},
                        ]
                plot_results_custom(scenarios, variables=vars, ss=self.ss, end_week = self.sim_duraion, fig_name='./png/convoi.png')




def __main__():
        
        medical_dict = {
                'vax': np.full(150, 1/52),
                'treat': np.zeros(150), 
                'covasim_res': pd.DataFrame({'I': [0.00013] * 150})
        }
        sir = sir_macro_obj(medical_dict, start_stayhome=5, end_stayhome=7, sim_duraion=150, verbose=True)
        best_policy, policy_history, loss_history = sir.find_best_ctax({'ctax_intensity': 0.5})
        sir.visualize()

if __name__ == '__main__':
    __main__()


"""
ctax: Consumption tax (containment policy)
H: Number of periods (weeks) to simulate 
pr_treat, pr_vacc: Probabilities of treatment and vaccination
pi1, pi2, pi3: Transmission probabilities for consumption, work, and other activities (e.g. meeting a neighbor or touching a contaminated surface)
eps: Initial infection rate
pidbar: Baseline death probability
pir: Recovery probability
kappa: Parameter for hospital capacity constraints
phi: labor productivity parameter
theta: Disutility of labor parameter
A: Productivity parameter
beta: Discount factor


ns, ni, nr: Labor supply for susceptible, infected, and recovered individuals
cs, ci, cr: Consumption for susceptible, infected, and recovered individuals
T: New infections
S, I, R, D: Population shares of Susceptible, Infected, Recovered, and Deceased
tau: Infection probability
Ur, Ui, Us: Value functions for recovered, infected, and susceptible individuals
mus: Multiplier on infection probability
lami, lams: Lagrange multipliers for infected and susceptible budget constraints
P: Total population (1 - D)
R1, R2, R3: Residuals for equilibrium conditions
C: Aggregate consumption (Consumption (C) equals output, which is productivity (A) times labor (N))
N: Aggregate labor supply (hours worked)
Neff: Effective labor supply (accounting for productivity loss of infected)
walras: Walras' law check (should be close to zero)
pid: Death probability
mortality: Mortality rate (pid / pir)


h (1E-4): Step size for numerical differentiation.
maxit (50): Maximum number of iterations for the solver.
noisy (False): If True, prints detailed information during solving.
H_U (None): Pre-computed Jacobian matrix (if available).
"""