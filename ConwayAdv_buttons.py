import random
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.widgets import Button

ON = 255
OFF = 0
vals = [ON, OFF]
MUTATION_PROB = 0.1
n = 100
RECOMBINATION_PROB = 0.3
ALPHA = 0.5
BETA = 0.5
LIFESPAN = 2

def random_grid(n: int) -> np.array:
    return np.random.choice(vals, n*n, p=[.2, .8]).reshape(n, n)

def pat_glider(grid: np.array, num_locations: int = 1):
    glider = np.array([
        [OFF, OFF, OFF, OFF, OFF, OFF, OFF, OFF, OFF, OFF],
        [OFF, OFF, OFF, OFF, OFF, OFF, OFF, OFF, OFF, OFF],
        [OFF, OFF, OFF, OFF, OFF, OFF, OFF, OFF, OFF, OFF],
        [OFF, OFF, OFF, OFF, OFF, OFF, OFF, OFF, OFF, OFF],
        [OFF, OFF, OFF, OFF, OFF, ON, ON, OFF, OFF, OFF],
        [OFF, OFF, OFF, OFF, OFF, OFF, ON, OFF, OFF, OFF],
        [OFF, OFF, OFF, OFF, ON, OFF, ON, OFF, OFF, OFF],
        [OFF, OFF, OFF, OFF, OFF, OFF, OFF, OFF, OFF, OFF],
        [OFF, OFF, OFF, OFF, OFF, OFF, OFF, OFF, OFF, OFF],
        [OFF, OFF, OFF, OFF, OFF, OFF, OFF, OFF, OFF, OFF]
    ])
    max_i = n - glider.shape[0]
    max_j = n - glider.shape[1]
    for _ in range(num_locations):
       i, j = random.randint(0, max_i), random.randint(0, max_j)
       grid[i:i+glider.shape[0], j:j+glider.shape[1]] = glider


def update_grid(frame_num, img, grid: np.array, n: int, germ_grid: np.array, germ_cells, genes):
    local_grid = grid.copy()
    local_germ_grid = germ_grid.copy()
    new_germ_cells = []
    for i in range(n):
        for j in range(n):
            total = int(((grid[i, (j-1) % n] + grid[i, (j+1) % n]) + grid[(i-1) % n, j] +
                         grid[(i+1) % n, j] + grid[(i+1) % n, (j+1) % n] + grid[(i-1) % n, (j-1) % n] +
                         grid[(i+1) % n, (j-1) % n] + grid[(i-1) % n, (j+1) % n])/ON)
            if grid[i, j] == ON and (total < 2 or total > 3):
                local_grid[i, j] = OFF
            elif total == 3:
                new_state, offspring_genes = germ_rule(grid, germ_grid, germ_cells, i, j)
                local_grid[i, j] = new_state
                local_germ_grid[i, j] = ON
                new_germ_cells.append((i, j, offspring_genes))
            elif total == 2:  # add inheritance rule
                new_state, offspring_genes = germ_rule(grid, germ_grid, germ_cells, i, j)
                local_grid[i, j] = new_state
                local_germ_grid[i, j] = germ_grid[i, j]
                if germ_grid[i, j] == ON:  # if this is a germ cell, apply genetic inheritance
                    if random.random() < 0.5:  # 50% chance of inheriting from parent germ cell
                        parent_genes = next(cell[2] for cell in germ_cells if cell[0] == i and cell[1] == j)
                        germ_cells.append((i, j, parent_genes))
                    else:  # 50% chance of generating new genes
                        offspring_genes = [random.gauss(mu=genes[k], sigma=0.1) for k in range(len(genes))]  # generate new genes
                        germ_cells.append((i, j, offspring_genes))
            else:
                local_germ_grid[i, j] = OFF
    img.set_data(local_grid)
    grid[:] = local_grid[:]
    germ_grid[:] = local_germ_grid[:]
    germ_cells.extend(new_germ_cells)
    return img

def health_measure(grid: np.array, germ_grid: np.array, germ_cells, i: int, j: int) -> int:
    """
    Calculates the health of a germ cell at (i, j) based on the number of consecutive frames in which it has been alive.
    """
    if germ_grid[i, j] == ON:
        if (i, j) in germ_cells:
            genes = germ_cells[(i, j)][2]  # retrieve genetic makeup of the germ cell
            if len(genes) < 5:
                return 0  # return 0 if the germ cell has insufficient genes to compute health
            lifespan = genes[4]  # retrieve lifespan gene value from genetic makeup of the germ cell
            if grid[i, j] == ON:  # germ cell is alive
                if germ_cells[(i, j)][0] < lifespan:  # germ cell is still within its lifespan
                    return germ_cells[(i, j)][0] + 1
                else:  # germ cell has reached the end of its lifespan
                    return 0
            else:  # germ cell is dead
                return 0
        else:  # not a germ cell
            return 0
    else:
        return 0

def germ_rule(grid: np.array, germ_grid: np.array, germ_cells: list, i: int, j: int):
    """
    Returns the new state of the germ cell at (i, j) based on the current state of the grid, germ grid, and germ cells.
    """
    if i*n+j < len(germ_cells):
        genes = germ_cells[i*n+j][2]
    else:
        genes = [MUTATION_PROB, RECOMBINATION_PROB, ALPHA, BETA, LIFESPAN]  # default genes
    mutation_prob = genes[0]
    recombination_prob = genes[1]
    alpha = genes[2]
    beta = genes[3]
    if germ_grid[i, j] == ON:  # if the germ cell is already ON, no need to change it
        return ON, genes
    elif germ_grid[i, j] == OFF:  # if the germ cell is OFF, apply stochastic mutation or recombination
        if random.random() < mutation_prob:  # apply mutation with probability specified by the genes
            offspring_genes = [random.gauss(mu=genes[k], sigma=0.1) for k in range(len(genes))]  # generate new genes by mutating the parent genes
            return ON, offspring_genes
        elif random.random() < recombination_prob:  # apply recombination with probability specified by the genes
            neighbors = [(i-1, j), (i+1, j), (i, j-1), (i, j+1), (i-1, j-1), (i-1, j+1), (i+1, j-1), (i+1, j+1)]
            valid_neighbors = [(x % n, y % n) for (x, y) in neighbors if germ_grid[x % n, y % n] == ON]
            if valid_neighbors:
                fitness_values = []
                for x, y in valid_neighbors:
                    total_germ_cells = np.sum(germ_grid[(x-1)%n:(x+2)%n, (y-1)%n:(y+2)%n]) - germ_grid[x, y]
                    health = health_measure(grid, germ_grid, germ_cells, x, y)
                    fitness = germ_grid[x, y] * (1 + alpha * total_germ_cells) * (1 + beta * health)
                    fitness_values.append(fitness)
                fitness_sum = sum(fitness_values)
                if fitness_sum > 0:
                    fitness_probs = [abs(fitness / fitness_sum) for fitness in fitness_values]
                    fitness_probs /= sum(fitness_probs)  # normalize probabilities
                    idx = np.random.choice(len(valid_neighbors), p=fitness_probs)
                    if 0 <= valid_neighbors[idx][0] < n and 0 <= valid_neighbors[idx][1] < n:
                        idx_germ_cells = valid_neighbors[idx][0]*n+valid_neighbors[idx][1]
                        if idx_germ_cells < len(germ_cells):
                            parent_genes = germ_cells[idx_germ_cells][2]
                        else:
                            parent_genes = []  
                    else:
                        parent_genes = []
                    if parent_genes == []:
                        offspring_genes = genes
                    else:
                        offspring_genes = [(parent_genes[k] if random.random() < 0.5 else genes[k]) for k in range(len(genes))]  # generate new genes by combining the parent genes with the current genes
                    return ON, offspring_genes
                else:
                    return OFF, genes
            else:
                return OFF, genes
        else:
            return OFF, genes
    else:
        return OFF, genes
def main():
    update_interval = 100
    grid = random_grid(n)
    germ_grid = np.zeros(n*n).reshape(n, n) # initialize germ grid to all OFF
    germ_cells = []
    genes = [MUTATION_PROB, RECOMBINATION_PROB, ALPHA, BETA, LIFESPAN]
    fig, ax = plt.subplots()
    img = ax.imshow(grid, interpolation='nearest')
    ani = animation.FuncAnimation(fig, update_grid, fargs=(img, grid, n, germ_grid, germ_cells, genes), 
                                   frames=10, interval=update_interval, save_count=50)

    def reset(event):
        nonlocal grid, germ_grid, germ_cells
        grid = random_grid(n)
        germ_grid[:] = 0
        germ_cells = []

    def add_glider(event):
        i, j = event.xdata, event.ydata
        pat_glider(i, j)
        pat_glider(i+10, j+10)
        pat_glider(i-10, j-10)
        pat_glider(i+10, j-10)
        pat_glider(i-10, j+10)
        update_grid(1,img, grid, n, germ_grid, germ_cells, genes)

    reset_ax = plt.axes([0.8, 0.05, 0.1, 0.075])
    reset_button = Button(reset_ax, 'Reset')
    reset_button.on_clicked(reset)

    glider_ax = plt.axes([0.8, 0.15, 0.1, 0.075])
    glider_button = Button(glider_ax, 'Add Glider')
    glider_button.on_clicked(add_glider)

    plt.show()

if __name__ == '__main__':
    main()

