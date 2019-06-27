import sys
import csv
from datetime import datetime
from ortools.linear_solver import pywraplp

def import_blocks():
    with open('../blockdistance.txt', 'r') as csvinput:
        blockinput = csv.reader(csvinput, delimiter='|')
        blocks = {}
        departure_seq = []

        for block in blockinput:
            blocks[int(block[0])] = [int(block[1]), block[2]]
            departure_seq.append([int(block[0]), block[2]])

        departure_seq.sort(key=lambda x: datetime.strptime(x[1], "%H:%M"))
        block_seq = []

        for i in departure_seq:
            block_seq.append(i[0])

    return blocks, block_seq


def import_vehicles():
    with open('../vehicles.txt', 'r') as csvinput:
        vehicleinput = csv.reader(csvinput, delimiter='|')
        vehicles = {}
        veh_list = []

        for vehicle in vehicleinput:
            vehicles[int(vehicle[0])] = [int(vehicle[1]), int(vehicle[2]), int(vehicle[3])]
            veh_list.append(int(vehicle[0]))

    return vehicles, veh_list


def create_matrix(blocks, vehicles):
    cost = []

    for vehicle in vehicles:
        avg_mileage = (vehicles[vehicle][1] - vehicles[vehicle][0]) / vehicles[vehicle][2]
        veh_block_cost = []

        print
        avg_mileage

        for block in blocks:
            cost_mileage = (avg_mileage - blocks[block][0]) ** 2
            veh_block_cost.append(cost_mileage)

        cost.append(veh_block_cost)

    return cost


def create_depot():
    pass


def main():
    blocks = import_blocks()[0]
    block_sort = import_blocks()[1]

    vehicles = import_vehicles()[0]
    veh_list = import_vehicles()[1]

    track1 = [5001, 5008, 5006]
    track2 = [5004, 5005, 5009]
    track3 = [5010, 5003, 5007]
    track4 = [5011, 5002, 5012]

    trackoccupation = [track1, track2, track3, track4]

    solver = pywraplp.Solver('SolveAssignmentProblemMIP', pywraplp.Solver.CBC_MIXED_INTEGER_PROGRAMMING)

    x = {}

    num_vehicles = len(vehicles)
    num_blocks = len(blocks)

    if num_blocks < num_vehicles:
        num_dummies = num_vehicles - num_blocks
        num_blocks_tot = num_vehicles
        for dummy in range(num_dummies):
            blocks[99000 + dummy] = [0, 0]
            block_sort.append(99000 + dummy)
    elif num_blocks == num_vehicles:
        num_blocks_tot = num_blocks
    else:
        sys.exit('Te weinig voertuigen beschikbaar')

    cost = create_matrix(blocks, vehicles)

    for i in range(num_vehicles):
        for j in range(num_blocks_tot):
            x[i, j] = solver.BoolVar('x[%i,%i]' % (i, j))

    print
    blocks
    print
    cost

    # Objective
    solver.Minimize(solver.Sum([cost[i][j] * x[i, j] for i in range(num_vehicles) for j in range(num_blocks_tot)]))

    # Constraints

    # Each vehicle is assigned to at most 1 block
    for i in range(num_vehicles):
        solver.Add(solver.Sum([x[i, j] for j in range(num_blocks_tot)]) <= 1)

    # Each block is assigned to exactly 1 vehicle
    for j in range(num_blocks_tot):
        solver.Add(solver.Sum([x[i, j] for i in range(num_vehicles)]) == 1)

    # Vehicle can not depart earlier than vehicle in front of it
    for track in trackoccupation:
        for i, vehicle in enumerate(vehicles):
            if vehicle in track:
                spot = track.index(vehicle)
                if spot > 0:
                    prev_veh = track[spot - 1]
                    prev_veh_index = veh_list.index(prev_veh)

                    for j, block in enumerate(blocks):
                        for k in range(min(block_sort.index(block) + 1, num_blocks_tot), num_blocks_tot):
                            # print str(i) + ',' + str(j) + ' - ' + str(prev_veh_index) + ',' + str(k)
                            solver.Add(solver.Sum([x[i, j] + x[prev_veh_index, k]]) <= 1)

    # Unassigned vehicle can not be in front of assigned vehicle
    for track in trackoccupation:
        for spot, vehicle in enumerate(track):
            if spot > 0:
                prev_veh = track[spot - 1]
                prev_veh_index = veh_list.index(prev_veh)
                i = veh_list.index(vehicle)
                solver.Add(solver.Sum([x[i, j] for j in range(num_blocks_tot)]) <= solver.Sum(
                    [x[prev_veh_index, k] for k in range(num_blocks_tot)]))

    # Solve
    sol = solver.Solve()

    if sol == solver.INFEASIBLE:
        print
        'Oplossing bestaat niet'

    print
    'Total costs = ', solver.Objective().Value()
    print
    ''
    for i in range(num_vehicles):
        for j in range(num_blocks_tot):
            if x[i, j].solution_value() > 0:
                print('Voertuig %d toegekend aan wagenloop %d.  Cost = %d' % (
                    vehicles.keys()[i],
                    blocks.keys()[j],
                    cost[i][j]))


main()