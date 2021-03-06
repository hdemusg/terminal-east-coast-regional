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
        global WALL, SUPPORT, TURRET, SCOUT, DEMOLISHER, INTERCEPTOR, MP, SP, UPGRADE, LEFTRIGHT, RIGHTLEFT
        WALL = config["unitInformation"][0]["shorthand"]
        SUPPORT = config["unitInformation"][1]["shorthand"]
        TURRET = config["unitInformation"][2]["shorthand"]
        SCOUT = config["unitInformation"][3]["shorthand"]
        DEMOLISHER = config["unitInformation"][4]["shorthand"]
        INTERCEPTOR = config["unitInformation"][5]["shorthand"]
        UPGRADE = "UPGRADE"
        LEFTRIGHT= "LEFTRIGHT"
        RIGHTLEFT = "RIGHTLEFT"
        MP = 1
        SP = 0
        # This is a good place to do initial setup
        self.scored_on_locations = []
        self.template = [] # Template for strategy
        self.initialize_template()
        self.attack_type = SCOUT
        self.attack_direction = LEFTRIGHT
        # If a structure gets below X% health, replace. Currently high value because it will sustain more dmg before getting actually removed
        self.replaceRatio = 0.75 

    def on_turn(self, turn_state):
        """
        This function is called every turn with the game state wrapper as
        an argument. The wrapper stores the state of the arena and has methods
        for querying its state, allocating your current resources as planned
        unit deployments, and transmitting your intended deployments to the
        game engine.
        """
        game_state = gamelib.GameState(self.config, turn_state)
        gamelib.debug_write('Performing turn {} of your custom algo strategy'.format(game_state.turn_number))
        game_state.suppress_warnings(True)  #Comment or remove this line to enable warnings.

        self.gun_strategy(game_state)
        game_state.submit_turn()


    """
    NOTE: All the methods after this point are part of the sample starter-algo
    strategy and can safely be replaced for your custom algo.
    """

    def addItems(self, coords, givenType):
         for loc in coords:
            tempStruct = {
                "struct": givenType,
                "pos": loc
            }
            self.template.append(tempStruct)

    # Hardcoded template strategy
    def initialize_template(self):
        initialwalls = [[0, 13], [2, 11], [26, 13], [3, 10], [4, 9], [5, 8], [6, 7], [7, 6], [18, 6], [8, 5], [17, 5], [9, 4], [10, 4], [11, 4], [12, 4], [13, 4], [14, 4], [15, 4], [16, 4]]
        initialTurrets = [[1, 12], [23, 12], [20, 9]]
        initialUpgrade = [[20, 9]]

        self.addItems(initialwalls, WALL)
        self.addItems(initialTurrets, TURRET)
        self.addItems(initialUpgrade, UPGRADE)

        turn2Walls = [[1, 13], [24, 13], [27, 13], [20, 8], [19, 7]]

        self.addItems(turn2Walls, WALL)

        turn3Walls = [[21, 11]]
        turn3Upgrade = [[23, 12]]

        self.addItems(turn3Walls, WALL)
        self.addItems(turn3Upgrade, UPGRADE)

        turn4Upgrade = [[1, 12]]
        turn4Walls = [[19, 9]]

        self.addItems(turn4Walls, WALL)
        self.addItems(turn4Upgrade, UPGRADE)

        turn5Turrets = [[25, 12], [25, 12], [21, 10]]
        turn5Walls = [[23, 13], [25, 13]]

        self.addItems(turn5Walls, WALL)
        self.addItems(turn5Turrets, TURRET)

        turn6Upgrade = [[1, 13]]
        turn6Turrets = [[2, 12]]
        turn6Walls = [[4, 13], [2, 13]]

        self.addItems(turn6Walls, WALL)
        self.addItems(turn6Turrets, TURRET)
        self.addItems(turn6Upgrade, UPGRADE)

        upgradeWalls = [[0, 13], [1, 13], [2, 13], [3, 13], [4, 13], [23, 13], [24, 13], [25, 13], [26, 13], [27, 13]]
        self.addItems(upgradeWalls, UPGRADE)

        leftOverTurrents = [[24, 12], [25, 12], [20, 10], [21, 10], [2, 13], [25, 12], [25, 12]]
        self.addItems(leftOverTurrents, UPGRADE)

    def gun_strategy(self, game_state):
        self.gun_defense(game_state)
        self.gun_attack(game_state)

    def gun_defense(self, game_state):
        # 1. Remove any structures below health % cutoff. (Needs to be first action or it might remove newly built buildings)
        # 2. Build out initial template
        # 3. Fortify initial template
        # 4. Add support buff units
        
        if game_state.get_resource(SP) == 0:
            return

        # 1. Remove low health structures
        # Generating all possible squares in our half
        locations = []
        for i in range(28):
            for j in range(14):
                if game_state.game_map.in_arena_bounds([i, j]):
                    locations.append([i, j])

        for loc in locations:
            currItem = game_state.game_map.__getitem__(loc)

            if not currItem or len(currItem) == 0:
                continue

            # Just destroyed structures are item 0. This line is why we need to remove first.
            dmgPercentage = currItem[0].health / currItem[0].max_health
            if dmgPercentage < self.replaceRatio:
                game_state.attempt_remove(loc)

        # 2. Build out initial template
        for item in self.template:

            if game_state.get_resource(SP) == 0:
                return

            if item["struct"] == UPGRADE:
                game_state.attempt_upgrade(item["pos"])
            else:
                game_state.attempt_spawn(item["struct"], item["pos"])

        if game_state.get_resource(SP) == 0:
            return

        # 3. Fortify initial template
        # Fortify Left + Right side
        fortificationTurrets = [[24, 12], [25, 12], [20, 10], [3, 13], [4, 13], [24, 13], [3, 12], [4, 12], [5, 12]]
        for loc in fortificationTurrets:
            game_state.attempt_spawn(TURRET, loc)
            game_state.attempt_upgrade(loc)

        #Fortify with walls
        fortificationWalls = [[19, 11], [20, 11], [21, 11], [19, 10], [19, 9], [26, 12], [5, 13]]
        for loc in fortificationWalls:
            game_state.attempt_spawn(WALL, loc)
            game_state.attempt_upgrade(loc)

        # 4. Add support buff units
        supportUnits = [[19, 8], [18, 7], [17, 6], [14, 5], [15, 5], [16, 5]]
        for loc in supportUnits:
            game_state.attempt_spawn(SUPPORT, loc)
            # game_state.attempt_upgrade(loc)

        supportUnits = [[18, 8], [17, 7], [15, 6], [16, 6], [12, 3], [13, 3], [14, 3], [15, 3]]
        for loc in supportUnits:
            game_state.attempt_spawn(SUPPORT, loc)

        return

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
        # if self.attackNextTurn:
            # We attacking - count dmg
        leftAttack = sum(
            [x.damage_i for x in game_state.get_attackers([1, 13], 0)])
        rightAttack = sum(
            [x.damage_i for x in game_state.get_attackers([26, 13], 0)])
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
        # else:
        #     self.tearDownGates(game_state)


    # Need to add more complex attack system
    def gun_attack(self, game_state):
        self.attack(game_state)

        # leftToRightSpawn = [12, 1]
        # rightToLeftSpawn = [14, 0]

        # spawn = leftToRightSpawn

        # # if self.attack_direction == LEFTRIGHT:
        # #     spawn = leftToRightSpawn
        # #     self.attack_direction =

        # if game_state.get_resource(MP) > 14:
        #     if self.attack_type == SCOUT:
        #         game_state.attempt_spawn(SCOUT, spawn, 1000)
        #         self.attack_type = DEMOLISHER
        #         return

        #     if self.attack_type == DEMOLISHER:
        #         game_state.attempt_spawn(DEMOLISHER, spawn, 1000)
        #         self.attack_type = SCOUT
        #         return

            


        # return



    def starter_strategy(self, game_state):
        """
        For defense we will use a spread out layout and some interceptors early on.
        We will place turrets near locations the opponent managed to score on.
        For offense we will use long range demolishers if they place stationary units near the enemy's front.
        If there are no stationary units to attack in the front, we will send Scouts to try and score quickly.
        """
        # First, place basic defenses
        self.build_defences(game_state)
        # Now build reactive defenses based on where the enemy scored


        # If the turn is less than 5, stall with interceptors and wait to see enemy's base
        if game_state.turn_number < 5:
            self.stall_with_interceptors(game_state)
        else:
            # Now let's analyze the enemy base to see where their defenses are concentrated.
            # If they have many units in the front we can build a line for our demolishers to attack them at long range.
            if self.detect_enemy_unit(game_state, unit_type=None, valid_x=None, valid_y=[14, 15]) > 10:
                self.demolisher_line_strategy(game_state)
            else:
                # They don't have many units in the front so lets figure out their least defended area and send Scouts there.

                # Only spawn Scouts every other turn
                # Sending more at once is better since attacks can only hit a single scout at a time
                if game_state.turn_number % 2 == 1:
                    # To simplify we will just check sending them from back left and right
                    scout_spawn_location_options = [[13, 0], [14, 0]]
                    best_location = self.least_damage_spawn_location(game_state, scout_spawn_location_options)
                    game_state.attempt_spawn(SCOUT, best_location, 1000)

                # Lastly, if we have spare SP, let's build some Factories to generate more resources
                support_locations = [[13, 2], [14, 2], [13, 3], [14, 3]]
                game_state.attempt_spawn(SUPPORT, support_locations)

    def build_defences(self, game_state):
        """
        Build basic defenses using hardcoded locations.
        Remember to defend corners and avoid placing units in the front where enemy demolishers can attack them.
        """
        # Useful tool for setting up your base locations: https://www.kevinbai.design/terminal-map-maker
        # More community tools available at: https://terminal.c1games.com/rules#Download

        # Place turrets that attack enemy units
        turret_locations = [[0, 13], [27, 13], [8, 11], [19, 11], [13, 11], [14, 11]]
        # attempt_spawn will try to spawn units if we have resources, and will check if a blocking unit is already there
        game_state.attempt_spawn(TURRET, turret_locations)
        
        # Place walls in front of turrets to soak up damage for them
        wall_locations = [[8, 12], [19, 12]]
        game_state.attempt_spawn(WALL, wall_locations)
        # upgrade walls so they soak more damage
        game_state.attempt_upgrade(wall_locations)

    def build_reactive_defense(self, game_state):
        """
        This function builds reactive defenses based on where the enemy scored on us from.
        We can track where the opponent scored by looking at events in action frames 
        as shown in the on_action_frame function
        """
        for location in self.scored_on_locations:
            # Build turret one space above so that it doesn't block our own edge spawn locations
            build_location = [location[0], location[1]+1]
            game_state.attempt_spawn(TURRET, build_location)

    def stall_with_interceptors(self, game_state):
        """
        Send out interceptors at random locations to defend our base from enemy moving units.
        """
        # We can spawn moving units on our edges so a list of all our edge locations
        friendly_edges = game_state.game_map.get_edge_locations(game_state.game_map.BOTTOM_LEFT) + game_state.game_map.get_edge_locations(game_state.game_map.BOTTOM_RIGHT)
        
        # Remove locations that are blocked by our own structures 
        # since we can't deploy units there.
        deploy_locations = self.filter_blocked_locations(friendly_edges, game_state)
        
        # While we have remaining MP to spend lets send out interceptors randomly.
        while game_state.get_resource(MP) >= game_state.type_cost(INTERCEPTOR)[MP] and len(deploy_locations) > 0:
            # Choose a random deploy location.
            deploy_index = random.randint(0, len(deploy_locations) - 1)
            deploy_location = deploy_locations[deploy_index]
            
            game_state.attempt_spawn(INTERCEPTOR, deploy_location)
            """
            We don't have to remove the location since multiple mobile 
            units can occupy the same space.
            """

    def demolisher_line_strategy(self, game_state):
        """
        Build a line of the cheapest stationary unit so our demolisher can attack from long range.
        """
        # First let's figure out the cheapest unit
        # We could just check the game rules, but this demonstrates how to use the GameUnit class
        stationary_units = [WALL, TURRET, SUPPORT]
        cheapest_unit = WALL
        for unit in stationary_units:
            unit_class = gamelib.GameUnit(unit, game_state.config)
            if unit_class.cost[game_state.MP] < gamelib.GameUnit(cheapest_unit, game_state.config).cost[game_state.MP]:
                cheapest_unit = unit

        # Now let's build out a line of stationary units. This will prevent our demolisher from running into the enemy base.
        # Instead they will stay at the perfect distance to attack the front two rows of the enemy base.
        for x in range(27, 5, -1):
            game_state.attempt_spawn(cheapest_unit, [x, 11])

        # Now spawn demolishers next to the line
        # By asking attempt_spawn to spawn 1000 units, it will essentially spawn as many as we have resources for
        game_state.attempt_spawn(DEMOLISHER, [24, 10], 1000)

    def least_damage_spawn_location(self, game_state, location_options):
        """
        This function will help us guess which location is the safest to spawn moving units from.
        It gets the path the unit will take then checks locations on that path to 
        estimate the path's damage risk.
        """
        damages = []
        # Get the damage estimate each path will take
        for location in location_options:
            path = game_state.find_path_to_edge(location)
            damage = 0
            for path_location in path:
                # Get number of enemy turrets that can attack each location and multiply by turret damage
                damage += len(game_state.get_attackers(path_location, 0)) * gamelib.GameUnit(TURRET, game_state.config).damage_i
            damages.append(damage)
        
        # Now just return the location that takes the least damage
        return location_options[damages.index(min(damages))]

    def detect_enemy_unit(self, game_state, unit_type=None, valid_x = None, valid_y = None):
        total_units = 0
        for location in game_state.game_map:
            if game_state.contains_stationary_unit(location):
                for unit in game_state.game_map[location]:
                    if unit.player_index == 1 and (unit_type is None or unit.unit_type == unit_type) and (valid_x is None or location[0] in valid_x) and (valid_y is None or location[1] in valid_y):
                        total_units += 1
        return total_units
        
    def filter_blocked_locations(self, locations, game_state):
        filtered = []
        for location in locations:
            if not game_state.contains_stationary_unit(location):
                filtered.append(location)
        return filtered

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
                gamelib.debug_write("All locations: {}".format(self.scored_on_locations))


if __name__ == "__main__":
    algo = AlgoStrategy()
    algo.start()
