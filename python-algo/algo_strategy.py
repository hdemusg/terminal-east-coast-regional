import gamelib
import random
import math
import warnings
from sys import maxsize
import json


"""
Most of the algo code you write will be in this file unless you create new
modules yourself. Start by modifying the 'on_turn' function.

Advanced strategy tips: 

  - You can analyze action frames by modifying on_action_frame function

  - The GameState.map object can be manually manipulated to create hypothetical 
  board states. Though, we recommended making a copy of the map to preserve 
  the actual current map state.
"""


class AlgoStrategy(gamelib.AlgoCore):

    lastScore = None
    attackNextTurn = False

    def __init__(self):
        super().__init__()
        seed = random.randrange(maxsize)
        random.seed(seed)
        gamelib.debug_write('Random seed: {}'.format(seed))

    def on_game_start(self, config):
        """ 
        Read in config and perform any initial setup here 
        """
        gamelib.debug_write('Configuring your custom algo strategy...')
        self.config = config
        global WALL, SUPPORT, TURRET, SCOUT, DEMOLISHER, INTERCEPTOR, MP, SP
        WALL = config["unitInformation"][0]["shorthand"]
        SUPPORT = config["unitInformation"][1]["shorthand"]
        TURRET = config["unitInformation"][2]["shorthand"]
        SCOUT = config["unitInformation"][3]["shorthand"]
        DEMOLISHER = config["unitInformation"][4]["shorthand"]
        INTERCEPTOR = config["unitInformation"][5]["shorthand"]
        self.gameMap = gamelib.game_map.GameMap(config)
        self.edges = self.gameMap.get_edges()
        self.edges[2].reverse()
        self.edges[3].reverse()
        self.allEdges = self.edges[2][2:-2]
        self.allEdges.extend(self.edges[3][2:-2])
        MP = 1
        SP = 0
        # This is a good place to do initial setup
        self.scored_on_locations = []

    def on_turn(self, turn_state):
        """
        This function is called every turn with the game state wrapper as
        an argument. The wrapper stores the state of the arena and has methods
        for querying its state, allocating your current resources as planned
        unit deployments, and transmitting your intended deployments to the
        game engine.
        """
        game_state = gamelib.GameState(self.config, turn_state)
        self.turn = game_state.turn_number
        gamelib.debug_write('Performing turn {} of your custom algo strategy'.format(
            game_state.turn_number))
        # game_state.suppress_warnings(True)  #Comment or remove this line to enable warnings.
        pointInc = 4 + (game_state.turn_number // 10)
        pointDec = game_state.get_resource(1) * 0.25
        # PARAM 1 - higher the number the more frequent, less powerful the attack
        attackNextTurn = pointInc < (pointDec * 2) #and (game_state.get_resource(0) > (game_state.turn_number//10) * 10 + 10)

        if game_state.turn_number == 0:
            self.firstTurn(game_state)
        if game_state.turn_number == 1:
            self.removeInitialExtra(game_state)

        # if self.lastScore != None:
        #     # Try scoring again - Greedy approach
        #     self.getPathOfLeastResistance(game_state)
        
        loc, dmg = self.least_damage_spawn_location(game_state, self.allEdges, True)
        
        if dmg == 0 and len(loc) > 0:
            # Path with no resistance
            attackNextTurn = False
            game_state.attempt_spawn(SCOUT, loc, 10000)
        
        # Only attack on enough SP
        if game_state.turn_number > 0:    
            if not attackNextTurn:
                self.buildDefense(game_state)
            else: 
                self.attack(game_state)
        
        self.attackNextTurn = attackNextTurn

        self.lastScore = None
        game_state.submit_turn()

    def removeInitialExtra(self, game_state):
        locations = [[4, 12], [12, 12], [15, 12], [23, 12], [4, 13], [23, 13]]
        game_state.attempt_remove(locations)

    # Static defense with dynamic strengthening
    def buildDefense(self, game_state):
        turretGroupOne = [[8,11],[19,11]]
        self.buildSuperTurrets(game_state, turretGroupOne)
        game_state.attempt_upgrade(turretGroupOne)
        self.buildGuidingWalls(game_state)
        turretGroupTwo = [[12, 10], [15,10]]
        self.buildProtectedTurrets(game_state, turretGroupTwo)
        turretGroupThree = [[3, 12], [24, 12], [4, 11], [23, 11]]
        game_state.attempt_spawn(TURRET, turretGroupThree)
        
        # Upgrades TG3 -> guiding walls row 1 -> TG2 -> outer guiding walls -> TG1 walls
        game_state.attempt_upgrade(turretGroupThree)
        guidingWalls = [[0, 13], [1, 13], [2, 13], [
            3, 13], [24, 13], [25, 13], [26, 13], [27, 13]]
        game_state.attempt_upgrade(guidingWalls)
        game_state.attempt_upgrade(turretGroupTwo)
        guidingWalls = [[4, 12], [23, 12], [5, 11], [22, 11], [
            5, 10], [22, 10], [6, 9], [21, 9], [7, 8], [20, 8]]
        game_state.attempt_upgrade(guidingWalls)
        supportWalls = [[8, 12], [19, 12], [7, 11], [9, 11], [12, 11], [
            15, 11], [18, 11], [20, 11], [11, 10], [13, 10], [14, 10], [16, 10]]
        game_state.attempt_upgrade(supportWalls)
        #game_state.attempt_spawn(INTERCEPTOR, [[8, 5], [19, 5]])
        

    # Builds walls on the side to guide enemy into the middle
    def buildGuidingWalls(self, game_state):
        bottomLeft = self.edges[2]
        bottomRight = self.edges[3]
        self.buildWallRow(bottomLeft[0][1], bottomLeft[0][0], 1, 4, game_state)
        self.buildWallRow(bottomRight[0][1], bottomRight[0][0], -1, 4, game_state)
        self.buildDiagonalWall(bottomLeft[1:3], 3, game_state)
        self.buildDiagonalWall(bottomRight[1:3], -3, game_state)
        self.buildDiagonalWall(bottomLeft[3:6], 2, game_state)
        self.buildDiagonalWall(bottomRight[3:6], -2, game_state)
    

    def buildDiagonalWall(self, edgeLocations, gap, game_state):
        locations = [[i[0] + gap, i[1]] for i in edgeLocations]
        game_state.attempt_spawn(WALL, locations)

    def buildWallRow(self, rowY, rowX, step, count, game_state):
        locations = [[rowX + i, rowY] for i in range(0, count*step, step)]
        game_state.attempt_spawn(WALL, locations)
        

    #        W 
    #      W T W
    #      Super turrets have this formation
    #      Assumes location is valid
    def buildProtectedTurrets(self, game_state, locations):
        for location in locations:
            x = location[0]
            y = location[1]
            walls = [[x-1, y], [x+1, y], [x, y+1]]
            self.tryBuild(game_state, walls, WALL)
            self.tryBuild(game_state, [location], TURRET)


    #      W W W      
    #      W T W
    #      Super turrets have this formation
    #      Assumes location is valid
    def buildSuperTurrets(self, game_state, locations):
        for location in locations:
            x = location[0]
            y = location[1]
            walls = [[x+i, y+1] for i in range(-1, 2)]
            walls.extend([[x-1, y], [x+1, y]])
            self.tryBuild(game_state, walls, WALL)
            self.tryBuild(game_state, [location], TURRET)

    def tryBuild(self, game_state, locations, unitType):
        for location in locations: 
            unit = game_state.contains_stationary_unit(location)
            if not unit:
                # Empty: We build
                game_state.attempt_spawn(unitType, [location])
            elif unit.unit_type == unitType and unit.health > unit.max_health * 0.3:
                # Already has structure and hp > half - keep
                continue
            else:
                # Wrong type or hp too low, we remove
                game_state.attempt_remove(location)    

    def tearDownGates(self, game_state):
        game_state.attempt_remove([[1, 13], [26, 13],[12, 10], [15, 10],[3, 12],[24, 12], [4, 11],[23, 11],[3, 12],[24, 12], [4, 11],[23, 11],[19, 11],[8, 12], [19, 12], [7, 11], [9, 11], [12, 11], [
            15, 11], [18, 11], [11, 10], [13, 10], [14, 10], [16, 10], [27, 13], [0, 13]])

    def _attack(self, game_state, structures, scout, demolisher, interceptor, wallCnt):
        sp = game_state.get_resource(0)
        # PARAM 2 - The lower the number, the more demolishers
        supportCount = round(max((sp - 16) // 3, 0))
        supports = structures[-supportCount:]
        walls = structures[:-supportCount]
        if (len(supports) > 0):
            game_state.attempt_spawn(SUPPORT, supports)
        # game_state.attempt_upgrade(supports)
        if (len(walls) > 0):
            game_state.attempt_spawn(WALL, walls)
        game_state.attempt_remove(structures)
        game_state.attempt_spawn(INTERCEPTOR, interceptor)
        if (wallCnt > 5):
            game_state.attempt_spawn(DEMOLISHER, demolisher, 100)
        else:
            c = round(game_state.get_resource(1) // 2)
            game_state.attempt_spawn(SCOUT, scout, c + 1)
        
    def attackLeft(self, game_state, cnt):
        core = [[8, 7], [9, 6], [10, 5], [11, 5], [12, 5], [13, 5], [14, 5], [15, 5], [
            16, 5], [17, 5], [18, 4], [12, 3], [13, 3], [14, 3], [15, 3], [11, 2], [2, 13], [3, 12], [4, 11], [5, 10], [6, 9], [7, 8]]
        scout = [[14, 0], [15, 1]]
        demolisher = [[17, 3]]
        interceptor = [[19, 5]]
        self._attack(game_state, core, scout, demolisher, interceptor, cnt)
    
    def attackRight(self, game_state, cnt):
        core = [[19, 7], [18, 6], [10, 5], [11, 5], [12, 5], [13, 5], [14, 5], [
            15, 5], [16, 5], [17, 5], [9, 4], [12, 3], [13, 3], [14, 3], [15, 3], [16, 2], [25, 13], [24, 12], [23, 11], [22, 10], [21, 9], [20, 8]]
        scout = [[13, 0], [12, 1]]
        demolisher = [[10, 3]]
        interceptor = [[8, 5]]
        self._attack(game_state, core, scout, demolisher, interceptor, cnt)

    # Modifies defense to favour attacking
    def attack(self, game_state):
        if self.attackNextTurn:
            # We attacking - count dmg
            leftAttack = sum([x.damage_i for x in game_state.get_attackers([1, 13], 0)])
            rightAttack = sum([x.damage_i for x in game_state.get_attackers([26, 13], 0)])
            leftZone = [[4, 18], [3, 17], [4, 17], [2, 16], [3, 16], [4, 16], [1, 15], [
                2, 15], [3, 15], [4, 15], [0, 14], [1, 14], [2, 14], [3, 14], [4, 14]]
            rightZone = [[23, 18], [23, 17], [24, 17], [23, 16], [24, 16], [25, 16], [23, 15], [
                24, 15], [25, 15], [26, 15], [23, 14], [24, 14], [25, 14], [26, 14], [27, 14]]
            leftZone = sum(
                [0 if not game_state.contains_stationary_unit(x) else 1 for x in leftZone])
            rightZone = sum(
                [0 if not game_state.contains_stationary_unit(x) else 1 for x in rightZone])
            if (leftAttack == rightAttack):
                # Randomly choose 
                # Count structures in immediate area to test if theres a counter
                if (leftZone >= rightZone):
                    self.attackRight(game_state, rightZone)
                else:
                    self.attackLeft(game_state, leftZone)
            elif (leftAttack > rightAttack):
                # Attack right
                self.attackRight(game_state, rightZone)
            else:
                # Attack left
                self.attackLeft(game_state, leftZone)
        else:
            self.tearDownGates(game_state)


    def getPathOfLeastResistance(self, game_state):
        fromLeft = self.least_damage_spawn_location(game_state, self.edges[2][5:10])
        fromRight = self.least_damage_spawn_location(game_state, self.edges[3][5:10])
        points = game_state.get_resource(1)
        if (fromLeft[1] == fromRight[1]):
            game_state.attempt_spawn(SCOUT, fromLeft[0], int(points / 2))
            game_state.attempt_spawn(SCOUT, fromRight[0], int(points / 2) + 1)
        else:
            game_state.attempt_spawn(
                SCOUT, fromRight[0] if fromRight[1] > fromLeft[1] else fromLeft[0], int(points))

    def least_damage_spawn_location(self, game_state, location_options, edgeOnly = False):
        """
        This function will help us guess which location is the safest to spawn moving units from.
        It gets the path the unit will take then checks locations on that path to
        estimate the path's damage risk.

        Can be optimized - DP

        """
        edges = [[[13, 27], [14, 27], [12, 26], [15, 26], [11, 25], [16, 25], [10, 24], [17, 24], [9, 23], [18, 23], [8, 22], [19, 22], [7, 21], [
            20, 21], [6, 20], [21, 20], [5, 19], [22, 19], [4, 18], [23, 18], [3, 17], [24, 17], [2, 16], [25, 16], [1, 15], [26, 15], [0, 14], [27, 14]]]
        damages = []
        # Get the damage estimate each path will take
        for location in location_options:
            path = game_state.find_path_to_edge(location)
            damage = 0
            if path != None and (not edgeOnly or path[-1] in edges):
                for path_location in path:
                    # Get number of enemy turrets that can attack each location and multiply by turret damage
                    damage += len(game_state.get_attackers(path_location, 0)) * \
                        gamelib.GameUnit(TURRET, game_state.config).damage_i
                damages.append(damage)

        # Now just return the location that takes the least damage

        if (len(damages) == 0):
            return ([], -1)

        # Opt
        return (location_options[damages.index(min(damages))], min(damages))

    def firstTurn(self, game_state):
        # Tries to get some free damage off if enemy has no defense
        gamelib.debug_write(game_state.get_resources())
        scouts = [[7, 6], [20, 6]]
        game_state.attempt_spawn(SCOUT, scouts, 2)  # 4 MP
        upgradedTurrets = [[8, 11], [19, 11]]
        game_state.attempt_spawn(TURRET, upgradedTurrets)  # 4 SP
        game_state.attempt_upgrade(upgradedTurrets)  # 8 SP
        normalTurrets = [[4, 12], [12, 12], [15, 12], [23, 12]]
        game_state.attempt_spawn(TURRET, normalTurrets)  # 8 SP
        walls = [[i, 13] for i in range(5)]
        walls.extend([[i, 13] for i in range(23, 28)])
        game_state.attempt_spawn(WALL, walls)  # 10 SP

    def on_action_frame(self, turn_string):
        """
        This is the action frame of the game. This function could be called 
        hundreds of times per turn and could slow the algo down so avoid putting slow code here.
        Processing the action frames is complicated so we only suggest it if you have time and experience.
        Full doc on format of a game frame at in json-docs.html in the root of the Starterkit.
        """
        # Let's record at what position we get scored on
        state = json.loads(turn_string)
        events = state["events"]
        breaches = events["breach"]
        for breach in breaches:
            location = breach[0]
            unit_owner_self = True if breach[4] == 1 else False
            # When parsing the frame data directly,
            # 1 is integer for yourself, 2 is opponent (StarterKit code uses 0, 1 as player_index instead)
            if not unit_owner_self:
                gamelib.debug_write("Got scored on at: {}".format(location))
                self.scored_on_locations.append(location)
                gamelib.debug_write(
                    "All locations: {}".format(self.scored_on_locations))
            else:
                gamelib.debug_write("Scored at: {}".format(location))
                self.lastScore = location


if __name__ == "__main__":
    algo = AlgoStrategy()
    algo.start()

# """
# NOTE: All the methods after this point are part of the sample starter-algo
# strategy and can safely be replaced for your custom algo.
# """

# def starter_strategy(self, game_state):
#     """
#     For defense we will use a spread out layout and some interceptors early on.
#     We will place turrets near locations the opponent managed to score on.
#     For offense we will use long range demolishers if they place stationary units near the enemy's front.
#     If there are no stationary units to attack in the front, we will send Scouts to try and score quickly.
#     """
#     # First, place basic defenses
#     self.build_defences(game_state)
#     # Now build reactive defenses based on where the enemy scored
#     self.build_reactive_defense(game_state)

#     # If the turn is less than 5, stall with interceptors and wait to see enemy's base
#     if game_state.turn_number < 5:
#         self.stall_with_interceptors(game_state)
#     else:
#         # Now let's analyze the enemy base to see where their defenses are concentrated.
#         # If they have many units in the front we can build a line for our demolishers to attack them at long range.
#         if self.detect_enemy_unit(game_state, unit_type=None, valid_x=None, valid_y=[14, 15]) > 10:
#             self.demolisher_line_strategy(game_state)
#         else:
#             # They don't have many units in the front so lets figure out their least defended area and send Scouts there.

#             # Only spawn Scouts every other turn
#             # Sending more at once is better since attacks can only hit a single scout at a time
#             if game_state.turn_number % 2 == 1:
#                 # To simplify we will just check sending them from back left and right
#                 scout_spawn_location_options = [[13, 0], [14, 0]]
#                 best_location = self.least_damage_spawn_location(
#                     game_state, scout_spawn_location_options)
#                 game_state.attempt_spawn(SCOUT, best_location, 1000)

#             # Lastly, if we have spare SP, let's build some Factories to generate more resources
#             support_locations = [[13, 2], [14, 2], [13, 3], [14, 3]]
#             game_state.attempt_spawn(SUPPORT, support_locations)

# def build_defences(self, game_state):
#     """
#     Build basic defenses using hardcoded locations.
#     Remember to defend corners and avoid placing units in the front where enemy demolishers can attack them.
#     """
#     # Useful tool for setting up your base locations: https://www.kevinbai.design/terminal-map-maker
#     # More community tools available at: https://terminal.c1games.com/rules#Download

#     # Place turrets that attack enemy units
#     turret_locations = [[0, 13], [27, 13], [
#         8, 11], [19, 11], [13, 11], [14, 11]]
#     # attempt_spawn will try to spawn units if we have resources, and will check if a blocking unit is already there
#     game_state.attempt_spawn(TURRET, turret_locations)

#     # Place walls in front of turrets to soak up damage for them
#     wall_locations = [[8, 12], [19, 12]]
#     game_state.attempt_spawn(WALL, wall_locations)
#     # upgrade walls so they soak more damage
#     game_state.attempt_upgrade(wall_locations)

# def build_reactive_defense(self, game_state):
#     """
#     This function builds reactive defenses based on where the enemy scored on us from.
#     We can track where the opponent scored by looking at events in action frames
#     as shown in the on_action_frame function
#     """
#     for location in self.scored_on_locations:
#         # Build turret one space above so that it doesn't block our own edge spawn locations
#         build_location = [location[0], location[1]+1]
#         game_state.attempt_spawn(TURRET, build_location)

# def stall_with_interceptors(self, game_state):
#     """
#     Send out interceptors at random locations to defend our base from enemy moving units.
#     """
#     # We can spawn moving units on our edges so a list of all our edge locations
#     friendly_edges = game_state.game_map.get_edge_locations(
#         game_state.game_map.BOTTOM_LEFT) + game_state.game_map.get_edge_locations(game_state.game_map.BOTTOM_RIGHT)

#     # Remove locations that are blocked by our own structures
#     # since we can't deploy units there.
#     deploy_locations = self.filter_blocked_locations(
#         friendly_edges, game_state)

#     # While we have remaining MP to spend lets send out interceptors randomly.
#     while game_state.get_resource(MP) >= game_state.type_cost(INTERCEPTOR)[MP] and len(deploy_locations) > 0:
#         # Choose a random deploy location.
#         deploy_index = random.randint(0, len(deploy_locations) - 1)
#         deploy_location = deploy_locations[deploy_index]

#         game_state.attempt_spawn(INTERCEPTOR, deploy_location)
#         """
#         We don't have to remove the location since multiple mobile
#         units can occupy the same space.
#         """

# def demolisher_line_strategy(self, game_state):
#     """
#     Build a line of the cheapest stationary unit so our demolisher can attack from long range.
#     """
#     # First let's figure out the cheapest unit
#     # We could just check the game rules, but this demonstrates how to use the GameUnit class
#     stationary_units = [WALL, TURRET, SUPPORT]
#     cheapest_unit = WALL
#     for unit in stationary_units:
#         unit_class = gamelib.GameUnit(unit, game_state.config)
#         if unit_class.cost[game_state.MP] < gamelib.GameUnit(cheapest_unit, game_state.config).cost[game_state.MP]:
#             cheapest_unit = unit

#     # Now let's build out a line of stationary units. This will prevent our demolisher from running into the enemy base.
#     # Instead they will stay at the perfect distance to attack the front two rows of the enemy base.
#     for x in range(27, 5, -1):
#         game_state.attempt_spawn(cheapest_unit, [x, 11])

#     # Now spawn demolishers next to the line
#     # By asking attempt_spawn to spawn 1000 units, it will essentially spawn as many as we have resources for
#     game_state.attempt_spawn(DEMOLISHER, [24, 10], 1000)

# def least_damage_spawn_location(self, game_state, location_options):
#     """
#     This function will help us guess which location is the safest to spawn moving units from.
#     It gets the path the unit will take then checks locations on that path to
#     estimate the path's damage risk.
#     """
#     damages = []
#     # Get the damage estimate each path will take
#     for location in location_options:
#         path = game_state.find_path_to_edge(location)
#         damage = 0
#         for path_location in path:
#             # Get number of enemy turrets that can attack each location and multiply by turret damage
#             damage += len(game_state.get_attackers(path_location, 0)) * \
#                 gamelib.GameUnit(TURRET, game_state.config).damage_i
#         damages.append(damage)

#     # Now just return the location that takes the least damage
#     return location_options[damages.index(min(damages))]

# def detect_enemy_unit(self, game_state, unit_type=None, valid_x=None, valid_y=None):
#     total_units = 0
#     for location in game_state.game_map:
#         if game_state.contains_stationary_unit(location):
#             for unit in game_state.game_map[location]:
#                 if unit.player_index == 1 and (unit_type is None or unit.unit_type == unit_type) and (valid_x is None or location[0] in valid_x) and (valid_y is None or location[1] in valid_y):
#                     total_units += 1
#     return total_units

# def filter_blocked_locations(self, locations, game_state):
#     filtered = []
#     for location in locations:
#         if not game_state.contains_stationary_unit(location):
#             filtered.append(location)
#     return filtered
