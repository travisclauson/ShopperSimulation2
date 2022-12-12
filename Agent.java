// README
// I couldn't figure out how to actually grab the items and put them in the cart
// For now, approaching a shelf is hacky, i just ram into it
// I initialize the shopping list myself at the bottom of this script (line 259)
// It should work for any food items except the back counters

import java.util.ArrayList;
import java.util.Arrays;
import java.lang.Math;
import java.util.Scanner;
import com.supermarket.*;
import java.io.*;
import java.lang.Thread;
import java.text.DecimalFormat;


public class Agent extends SupermarketComponentImpl {
	public Agent() {
		super();
		shouldRunExecutionLoop = true;
	}

	public static SupermarketObservation obsv = new SupermarketObservation();

	// variables
	int playerIndex;
	int cartIndex;
	int idealMoveDirection; //0=N, 1=S, 2=E, 3=W, 4=interact, 5=toggleCart, otherwise=null
	int actualMoveDirection;
	int count = 0;
	double[] goalCoordinates = {0.0,0.0};
	double[] adjustedGoalCoordinates = {0.0,0.0};
	double[] playerCoordinates = {0.0, 0.0};
	String goalLocation = "";
	String currentAction = "";
	boolean setupDone = false;
	int uniqueItemsInCart = 0;
	int numOfUniqueItemLeft = 0;
	ArrayList<String> actionList = new ArrayList<String>(
            Arrays.asList("Finding Carts", "Shopping", "Checking Out", "Exiting"));
	ArrayList <String> pathGoalList;
	ArrayList <double[]> pathGoalCoordinates;
	String currentPlanLocation = "";
	int facingDir = 6;
	// double dropCartY = 0.0;

	int currentShelfIndex = 0;
	int shoppingListLength = 0;
	boolean shelfItem = false;
	boolean counterItem = false;
	boolean usingAlternatePath = false;
	boolean playerCollisionNormViolated = false;
	boolean shopliftingNormChecked = false;

	// position constants
	double yShoppingAdjust = 2.5;
	double xShoppingAdjust = -1.0;
	double oneStep = 0.15;
	double shelfBuffer = 1; // for avoid collision while pick up item from shelf
	double wallXmin = 0.5;
	double wallXmax = 18.89;
	double wallYmin = 2.1;
	double wallYmax = 24.1;
	double exitX = -2;
	double aisleHeight = 4;

	// state constants
	boolean isMoving = true;
	boolean hasGoal = false;
	String currentSubAction = "";
	ArrayList<Integer> subActionList;
	int numOfNorms = 9; // total number of norms
	boolean[][] possibleMoveDirections = new boolean[numOfNorms][7]; //each rows for one unique norm
	int tempMoveDirection = 6;
	int[] checkOutCancelationThreshold = {3, 3};
	int[] counterCancelationThreshold = {17, 18};
    int collisionPlayerIndex = -1;
	boolean skipCheckNorm = false;

	//Custom Scenario
	boolean customShoppingList = true;
	String customFoodItem = "apples";//"brie cheese"; //"brie cheese";

	//print statements on/off
	boolean printPlayerCoordinates = false;
	boolean printGoalShelfCoordinates = false;
	boolean printLoop = false;
	boolean printLocationError = false;
	boolean printCartPosition = false;
	boolean printAllNormResults = false;
	boolean printPathPlan = true;
	DecimalFormat df = new DecimalFormat("##.##");


	@Override
	protected void executionLoop() {
		if (!setupDone) setup();
		if (printLoop) System.out.println("Loop: " + Integer.toString(count));
		
		//SENSE
		updateObservation();

		//DECIDE - where is the next goal, how do we get there, set moveDirection
		idealMoveDirection = decideIdealAction();
		// System.out.print("path in main loop: ");
		// System.out.println(pathGoalList);
		// System.out.println(playerCoordinates[1]);
		if (idealMoveDirection > 5) {
			actualMoveDirection = idealMoveDirection;
		} else {
			int x = 0; //checkNorms();
			// actualMoveDirection = decideActualAction(); //based on allowed decisions from norms
		}
		actualMoveDirection = idealMoveDirection;
		// aupdate action queue
		updateActionQueue(actualMoveDirection);
	
		//MOVE - move based on moveDirection
		act(actualMoveDirection);
		count+=1;
	}



	public void setup(){ 
		updateObservation();

		playerIndex = obsv.players.length - 1;
		System.out.println("\nWe are initialized as Player: " + playerIndex + "\n");
		System.out.println("\nAction List:");
		System.out.println(actionList + "\n");

		if (!customShoppingList) {
			shoppingListLength = obsv.players[playerIndex].shopping_list.length;
			numOfUniqueItemLeft = shoppingListLength;
		} else {
			shoppingListLength = 1;
			numOfUniqueItemLeft = 1;
		}
		System.out.println("Shopping List:");
		for(int i=0; i<shoppingListLength; i++){
			System.out.println(
			String.valueOf(obsv.players[playerIndex].list_quant[i]) + " - " + 
			obsv.players[playerIndex].shopping_list[i] + "\n");
		}

		// setGoalLocation();
		buildPathPlan(); //Build Plan to grab cart
		// TODO: Generate queue for finding cart 
		setupDone = true;
	}

	/////////// CORE FUNCTIONS ///////////

	//Decide what our ideal action is
	public int decideIdealAction(){ 
		int direction = 6;
		if (pathGoalList.isEmpty()) {
			// System.out.println("pathGoalList is empty");
			switch (actionList.get(0)) { // generate queue based on current action
				case "Finding Carts": // reached when finished finding cart 
					actionList.remove(0);
					cartIndex = obsv.players[playerIndex].curr_cart;
					if (numOfUniqueItemLeft > 0) {
						buildPathPlan();
						System.out.println("build path after find cart");
						System.out.println(actionList);
					}
					break;
				case "Shopping": 
					numOfUniqueItemLeft--;
					if (numOfUniqueItemLeft > 0) {
						buildPathPlan();
						System.out.println("get another food");
					} else {
						actionList.remove(0);
						System.out.println("go to check out");
						findRegisterCoordinates();
						buildPathPlan();
					}
					break;
				case "Checking Out":
					actionList.remove(0);
					buildPathPlan();
					break;
				case "Exiting": // should never be reached
					break; 
			}

			System.out.println("Generate new queue");
			// System.out.print("path: ");
			// System.out.println(pathGoalList);
		}
		return get_direction_from_goal_list();
	}

	//Outputs the best moveDirection considering what is ideal and the norms
	public void checkNorms(){
		int tempMoveDirection;
		// intialize each move direciton as true
		for (boolean[] row: possibleMoveDirections) 
			Arrays.fill(row, true);

		// nomrs for navigation
		wallCollisionNorm();
		objectCollisionNorm();
		playerCollisionNorm(); //includes personal space norm
		entranceOnlyNorm();
		blockingExitNorm();
		unattendedCartNorm();


		// norms for interaction
		cartTheftNorm();
		shopliftingNorm();
		oneCartOnlyNorm();

		// Finally check if interaction is canceled
		interactionCancellationNorm();
	}

	public int decideActualAction(){
		int count =1;
		//intialize the summed array
		boolean[] summedPossibleMoveDirections = {true, true, true, true, true, true, true};

		for (int i = 0; i < possibleMoveDirections[0].length; i++){ //Fill in the summed array
			if(printAllNormResults) System.out.print("\nDirection " + i + ": ");
			count = 1;
			for (boolean[] norm : possibleMoveDirections){
				if (norm[i] == false) //if any norms violate a certain direction, set that sumPossibleDirection false
					summedPossibleMoveDirections[i] = false;
				if(printAllNormResults) 
					System.out.print("Norm " + count + ": " + norm[i] + "  ");
				count++;
			}
		}
		
		if (summedPossibleMoveDirections[idealMoveDirection]){
			if(printAllNormResults) System.out.println("Ideal action: " + idealMoveDirection + " is valid");
			return idealMoveDirection;
		} else {
			System.out.println("ideal direction " + idealMoveDirection + " breaks norm");
			if (idealMoveDirection < 3 && idealMoveDirection > -1)
				return find_actual_navigation_direction(summedPossibleMoveDirections);
			else {
				System.out.println("No actions are allowed at the moment");
				return 6;
			}
		}
	}

	public int find_actual_navigation_direction (boolean[] summedPossibleMoveDirections) {
		if (actionList.get(0) == "Shopping" &&
			pathGoalList.get(0) == "Aisle" && playerCollisionNormViolated) {
			// generate new queue to walk around, args?
			tempMoveDirection = get_direction_from_goal_list();
		} else if (actionList.get(0) == "Shopping" &&
			pathGoalList.get(0) == "Aisle Hub" && playerCollisionNormViolated) {
			// generate new queue to walk around, args?
			tempMoveDirection = get_direction_from_goal_list();
		} // TODO: other norm solutions

		// check if valid direction, if yes set direction
		if (!summedPossibleMoveDirections[tempMoveDirection]) {
			for(int j = 0; j < summedPossibleMoveDirections.length; j++) {
				if(summedPossibleMoveDirections[j]){
					tempMoveDirection = j;
					System.out.println("Settled for a new action: " + tempMoveDirection);
				} else {
					tempMoveDirection = 6;
					System.out.println("No actions are allowed at the moment");
				}
			}
		}
		return tempMoveDirection;
	}
	
	//Literally just walk in the direction that Decide() detirmines, interact if neccesary
	public void act(int dir){
		if (dir == 0) goNorth();
		else if (dir == 1) goSouth(); 
		else if (dir == 2) goEast(); 
		else if (dir == 3) goWest();
		else if (dir == 4) {interactWithObject(); sleep(200);}
		else if (dir == 5) {toggleShoppingCart(); sleep(200);}
		else if (dir == 7) goEast();
		else if (dir == 8) goWest(); 
		else if (dir == 9) goNorth();
		else if (dir == 10) goSouth(); 
	}

	/////////// SECONDARY FUNCTIONS ///////////

	public void buildPathPlan() { //I realized my logic is designed for food items, not sure how to adjust for Carts, Counters, Registers
		String currAction = actionList.get(0);
		System.out.println("Building Path Plan");
		pathGoalList = new ArrayList<String>();
		// pathGoalList.add("Current Location");
		double tempArray[] = playerCoordinates; //since I cannot figure out how to manually add an array to arrayList ... arrayList.add({1.0,2.0}); won't work
		pathGoalCoordinates = new ArrayList<double[]>();
		// pathGoalCoordinates.add(tempArray);
		String currentPlanLocation = detirmineRelativeLocation(adjustedGoalCoordinates, playerCoordinates);
		while(currentPlanLocation != "Goal Location"){
			int listLength = pathGoalCoordinates.size();
			switch (currentPlanLocation) {
				case ("Wrong Aisle"): //update X
					int hub = whichHubToUse();
					pathGoalList.add("Aisle Hub"); //  + hub
					if (hub == 1){
						tempArray[0] = 4.25;//4.25 is the middle of the front hub, then use the last Y value set since just walking north/south
						pathGoalCoordinates.add(new double[] {tempArray[0], tempArray[1]}); 
					} else {
						tempArray[0] = 16.25; //16.25 is the middle of the rear hub
						pathGoalCoordinates.add(new double[] {tempArray[0], tempArray[1]});
					}
					currentPlanLocation = "Aisle Hub";
					break;

				case ("Aisle Hub"): //update Y
					if (actionList.get(0) == "Finding Carts") {
						tempArray[1] = 17;
						pathGoalList.add("Goal Vertical");
					} else if (actionList.get(0) == "Checking Out") { // || actionList.get(0) == "Exiting") {
						tempArray[1] = adjustedGoalCoordinates[1];
						pathGoalList.add("Goal Vertical");
					} else if (actionList.get(0) == "Shopping") { // Queue for shop for an item
						findFoodCoordinates();
						int aisleIndex = getAisleIndex(adjustedGoalCoordinates);
						//System.out.println("Goal Coordinates for Food item: " + goalCoordinates[0] + ", " + goalCoordinates[1]);
						pathGoalList.add("Aisle");
						tempArray[1] = 4 * aisleIndex - 1;
						pathGoalCoordinates.add(new double[] {tempArray[0], tempArray[1]});

						pathGoalList.add("Goal Location");// 
						tempArray[0] = adjustedGoalCoordinates[0]; // should be the recipe for middle of the aisle
						pathGoalCoordinates.add(new double[] {tempArray[0], tempArray[1]});

						pathGoalList.add("Toggle"); // drop cart
						pathGoalCoordinates.add(new double[] {tempArray[0], tempArray[1]});

						pathGoalList.add("checkFacingDirection");
						pathGoalCoordinates.add(new double[] {tempArray[0], tempArray[1]});

						pathGoalList.add("Goal Vertical"); // go to shelf
						tempArray[1] = 4 * aisleIndex - 1.3;
						pathGoalCoordinates.add(new double[] {tempArray[0], tempArray[1]});

						pathGoalList.add("Interact"); // pick up item
						pathGoalCoordinates.add(new double[] {tempArray[0], tempArray[1]});

						pathGoalList.add("Interact"); // pick up item
						pathGoalCoordinates.add(new double[] {tempArray[0], tempArray[1]});

						pathGoalList.add("Goal Vertical"); // go to cart
						tempArray[1] = 4 * aisleIndex - 1;
						pathGoalCoordinates.add(new double[] {tempArray[0], tempArray[1]});

						pathGoalList.add("turnToFaceCart"); // face cart
						pathGoalCoordinates.add(new double[] {tempArray[0], tempArray[1]});

						pathGoalList.add("Interact"); // put item
						pathGoalCoordinates.add(new double[] {tempArray[0], tempArray[1]});

						pathGoalList.add("Interact"); // put item
						pathGoalCoordinates.add(new double[] {tempArray[0], tempArray[1]});

						pathGoalList.add("Toggle"); // grab cart
						pathGoalCoordinates.add(new double[] {tempArray[0], tempArray[1]});

						currentPlanLocation = "Goal Location";
						break;
					}
					pathGoalCoordinates.add(new double[] {tempArray[0], tempArray[1]});
					currentPlanLocation = "Correct Aisle";
					break;

				case ("Correct Aisle"): //update X
					if (actionList.get(0) == "Finding Carts") {
						tempArray[0] = 1;
						pathGoalList.add("Goal Horizontal");
						pathGoalCoordinates.add(new double[] {tempArray[0], tempArray[1]}); 
						tempArray[1] = 17.75;
						pathGoalList.add("Goal Vertical");
						pathGoalCoordinates.add(new double[] {tempArray[0], tempArray[1]}); 
						pathGoalList.add("Interact");
						pathGoalCoordinates.add(new double[] {0, 0}); 
						pathGoalList.add("Interact");
						pathGoalCoordinates.add(new double[] {0, 0}); 
					} else if (actionList.get(0) == "Checking Out") {
						tempArray[0] = adjustedGoalCoordinates[0];
						pathGoalList.add("Goal Horizontal");
						pathGoalCoordinates.add(new double[] {tempArray[0], tempArray[1]});

						pathGoalList.add("Toggle"); // drop cart
						pathGoalCoordinates.add(new double[] {tempArray[0], tempArray[1]});

						pathGoalList.add("checkFacingDirection");
						pathGoalCoordinates.add(new double[] {tempArray[0], tempArray[1]});

						pathGoalList.add("9"); // go to register
						pathGoalCoordinates.add(new double[] {tempArray[0], tempArray[1]});

						pathGoalList.add("Interact"); // check out
						pathGoalCoordinates.add(new double[] {tempArray[0], tempArray[1]});

						pathGoalList.add("Interact"); // check out
						pathGoalCoordinates.add(new double[] {tempArray[0], tempArray[1]});

						pathGoalList.add("10"); // go to register
						pathGoalCoordinates.add(new double[] {tempArray[0], tempArray[1]});

						pathGoalList.add("turnToFaceCart"); // face cart
						pathGoalCoordinates.add(new double[] {tempArray[0], tempArray[1]});

						pathGoalList.add("Toggle"); // grab cart
						pathGoalCoordinates.add(new double[] {tempArray[0], tempArray[1]});

						// tempArray[0] = exitX;
						// pathGoalList.add("Goal Horizontal");
						// pathGoalCoordinates.add(new double[] {tempArray[0], tempArray[1]});
						currentPlanLocation = "Goal Location";
						
					} else if (actionList.get(0) == "Shopping"){
						pathGoalList.add("Goal Location");
						tempArray[0] = adjustedGoalCoordinates[0];
						pathGoalCoordinates.add(new double[] {tempArray[0], tempArray[1]});
					}
					currentPlanLocation = "Goal Location";
					break;

				case ("Front of Store"): //update X
					if (actionList.get(0) == "Exiting") {
						tempArray[0] = exitX;
						pathGoalList.add("Goal Horizontal");
						pathGoalCoordinates.add(new double[] {tempArray[0], tempArray[1]});
						currentPlanLocation = "Goal Location";
					} else {
						pathGoalList.add("Aisle Hub"); // 1
						tempArray[0] = 3.8;
						pathGoalCoordinates.add(new double[] {tempArray[0], tempArray[1]}); 
						currentPlanLocation = "Aisle Hub";
					}
					break;

				case ("Back of Store"): //update X
					pathGoalList.add("Aisle Hub"); // 2
					tempArray[0] = 16.25;
					// new int[]{ 1,2,3,4,5,6,7,8,9,10 }
					pathGoalCoordinates.add(new double[] {tempArray[0], tempArray[1]});
					currentPlanLocation = "Aisle Hub";
					break;
			}
			// System.out.println("Path Coordinates List:");
			// for(double paths[]: pathGoalCoordinates)
			// System.out.println(paths[0] + ", " + paths[1]);
		}
		System.out.println("path goal coordinates: " + pathGoalCoordinates.get(0)[0] + ", " + pathGoalCoordinates.get(0)[1]);
		if(printPathPlan) System.out.println("Path List: " + pathGoalList);
		System.out.println("Path Coordinates List:");
		for(double paths[] : pathGoalCoordinates){
			System.out.println(paths[0] + ", " + paths[1]);
		}
	}

	public void updateActionQueue(int actualMoveDirection) {
		if (actualMoveDirection > 3 && actualMoveDirection < 11) {
			// skipCheckNorm = false;
			pathGoalList.remove(0);
			pathGoalCoordinates.remove(0);
		} else if (actualMoveDirection <= 3 && actualMoveDirection >= 0){
			double[] nextLocation = getNextLocation(actualMoveDirection, playerCoordinates[0], playerCoordinates[1]);
			switch (pathGoalList.get(0)) {
				case "Aisle": 
					if ((actualMoveDirection == 0 && playerCoordinates[1] <= pathGoalCoordinates.get(0)[1] + oneStep) ||
						(actualMoveDirection == 1 && playerCoordinates[1] >= pathGoalCoordinates.get(0)[1] - oneStep)) {
						pathGoalList.remove(0);
						pathGoalCoordinates.remove(0);
						System.out.println("Reached Aisle");
					}
					break;
				case "Aisle Hub":
					if ((actualMoveDirection == 2 && nextLocation[0] >= pathGoalCoordinates.get(0)[0]) ||
						(actualMoveDirection == 3 && nextLocation[0] <= pathGoalCoordinates.get(0)[0])) {
						pathGoalList.remove(0);
						pathGoalCoordinates.remove(0);
						System.out.println("Reached Aisle Hub");
					} else {
						System.out.println("Moving to Aisle Hub");
					}
					break;
				case "Goal Location": // only need this case?
					if ((actualMoveDirection == 0 && nextLocation[1] <= pathGoalCoordinates.get(0)[1]) ||
						(actualMoveDirection == 1 && nextLocation[1] >= pathGoalCoordinates.get(0)[1]) ||
						(actualMoveDirection == 2 && nextLocation[0] >= pathGoalCoordinates.get(0)[0]) ||
						(actualMoveDirection == 3 && nextLocation[0] <= pathGoalCoordinates.get(0)[0])) {
						pathGoalList.remove(0);
						pathGoalCoordinates.remove(0);
						System.out.println("Reached Goal Location");
					}
					break;
				case "Goal Vertical": 
					if ((actualMoveDirection == 0 && playerCoordinates[1] <= pathGoalCoordinates.get(0)[1] + oneStep) ||
						(actualMoveDirection == 1 && playerCoordinates[1] >= pathGoalCoordinates.get(0)[1] - oneStep)) {
						pathGoalList.remove(0);
						pathGoalCoordinates.remove(0);
						System.out.println("Reached Goal Vertical");
					}
					System.out.println("moving to vertical");
					break;	
				case "Goal Horizontal": 
					if (((actualMoveDirection == 3 && playerCoordinates[0] <= pathGoalCoordinates.get(0)[0] + oneStep) ||
						(actualMoveDirection == 2 && playerCoordinates[0] >= pathGoalCoordinates.get(0)[0] - oneStep))){
						pathGoalList.remove(0);
						pathGoalCoordinates.remove(0);

						System.out.println("Reached Goal Horizontal");
						// System.out.println(actualMoveDirection);

						// System.out.print("playerCoordinates[0]: ");
						// System.out.println(playerCoordinates[0]);
						// System.out.print("pathGoalCoordinates.get(0)[0]: ");
						// System.out.println(pathGoalCoordinates.get(0)[0]);
					} else {
						System.out.println("Moving to horizontal");
					}
					break;
				default:
					break;
			}
		}
	}

	public String detirmineRelativeLocation(double goalCoordinates[], double currentCoordinates[]) {
		double xGoal = goalCoordinates[0];
		double yGoal = goalCoordinates[1];
		double xPos = currentCoordinates[0];
		double yPos = currentCoordinates[1];

		int goalAisle = getAisleIndex(goalCoordinates);
		int currentAisle = getAisleIndex(currentCoordinates);
		if (currentAisle >= 1 && currentAisle <= 6)
			if (goalAisle == currentAisle) return "Correct Aisle";
			else return "Wrong Aisle";
		else if (currentAisle == 8 || currentAisle==9) return "Aisle Hub";
		else if (currentAisle == 7) return "Front of Store";
		else if (currentAisle == 10) return "Back of Store"; 
		else return "Error Detirmining Relative Location";
	}

	public int get_direction_from_goal_list() {
		int direction = 6;
		switch (pathGoalList.get(0)) { // TODO: cases redundant? need refactor
			case "Aisle": 
				if (pathGoalCoordinates.get(0)[1] > playerCoordinates[1]) direction = 1;
				else direction = 0;
				System.out.println("Aisle");
				break;
			case "Aisle Hub":
				if (pathGoalCoordinates.get(0)[0] > playerCoordinates[0]) direction = 2;
				else direction = 3;
				System.out.println("Aisle Hub");
				break;
			case "Goal Horizontal":
				if (pathGoalCoordinates.get(0)[0] > playerCoordinates[0]) direction = 2;
				else direction = 3;
				System.out.println("Goal Horizontal");
				break;
			case "Goal Vertical":
				if (pathGoalCoordinates.get(0)[1] >= playerCoordinates[1]) direction = 1;
				else direction = 0;
				System.out.println(" Goal Vertical");
				break;
			case "Goal Location":
				if (pathGoalCoordinates.get(0)[0] > playerCoordinates[0]) direction = 2;
				else direction = 3;
				System.out.println(" Goal Location");
				break;
			case "Interact":
				direction = 4;
				System.out.println("********Interact");
				break;
			case "Toggle":
				direction = 5;
				System.out.println("********Toggle");
				break;
			case "checkFacingDirection":
				facingDir = obsv.players[playerIndex].direction;
				System.out.print("********Checked face direction: ");
				System.out.println(facingDir);
				break;
			case "turnToFaceCart":
				skipCheckNorm = true;
				if (facingDir == 2) {
					pathGoalList.remove(0);
					pathGoalCoordinates.remove(0);

					// direction = 8; // east and skipCheckNorm
					direction = 7; 

					pathGoalList.add(0, "7"); // go to register
					pathGoalCoordinates.add(0, new double[] {0.0, 0.0});

					// pathGoalList.add(0, "8"); // go to register
					// pathGoalCoordinates.add(0, new double[] {0.0, 0.0});

					// goWest(); goEast(); goEast();
				} else if (facingDir == 3) {
					pathGoalList.remove(0);
					pathGoalCoordinates.remove(0);
					direction = 7; // west and skipCheckNorm
					pathGoalList.add(0, "8"); // go to register
					pathGoalCoordinates.add(0, new double[] {0.0, 0.0});
					pathGoalList.add(0, "7"); // go to register
					pathGoalCoordinates.add(0, new double[] {0.0, 0.0});
				}
				System.out.print("********Turn to face cart: ");
				System.out.println(facingDir);
				System.out.print("********Can interact with cart: ");
				System.out.println(obsv.carts[cartIndex].canInteract(obsv.players[playerIndex]));
				System.out.print("********Current face direction: ");
				System.out.println(obsv.players[playerIndex].direction);
				// direction = 6;
				facingDir = 6;
				break;
			case "7":
				direction = 7;
				break;
			case "8":
				direction = 8;
				break;
			case "9":
				direction = 9;
				break;
			case "10":
				direction = 10;
				break;
			// case "North":
			// 	// goNorth();
			// 	direction = 0;
			// 	skipCheckNorm = true;
			// 	break;
			// case "South":
			// 	// goSouth();
			// 	direction = 1;
			// 	skipCheckNorm = true;
			// 	break;
			default:
				direction = 6;
				break;
		}
		return direction;
	}

	public int whichHubToUse(){
		double xPos = obsv.players[playerIndex].position[0];

		if (!usingAlternatePath) {//when nothing is blocking our path (normal scenario) use closest aisle hub
			if(xPos < 16) return 1; //Left Aisle Hub (1)
			else return 2; //Right Aisle Hub
		}
		else { //Use opposite aisle hub
			if(xPos < 16) return 2; 
			else return 1;
		}
	}

	public int getAisleIndex(double coordinates[]){ //returns the region of the store of the coordinates given
		// 1-6  = Aisles top->bottom, 7 = front of store, 8 = Front Hub, 9 = Back Hub, 10 = Back of Store
		double xPos = coordinates[0];
		double yPos = coordinates[1];
		//System.out.println("Coordinates: " + xPos + ", " + yPos);
		if (xPos >= 5.5 && xPos <= 14.5){ //in an aisle
			for (int i = 1; i <= 6; i++) {
				double aisleTop = 0.5 + 4.*(i - 1);
       			double aisleBottom = 0.5 + 4.*i;
				if (yPos >= aisleTop && yPos <=aisleBottom) return i;
			}
		}
		else if(xPos <= 3.75) return 7;
		else if(obsv.inAisleHub(playerIndex)) return 8;
		else if(obsv.inRearAisleHub(playerIndex)) return 9;
		else if(xPos >= 16.5) return 10;
		else System.out.println("Get Aisle Index Failed");
		return 0;
	}

	//Discover what our goal location is: exit, shelf x, register etc.
	// public void setGoalLocation() {
	// 	hasGoal = true;
	// 	if (currentAction != actionList.get(0)) {
	// 		String lastAction = currentAction;
	// 		currentAction = actionList.get(0);
	// 		System.out.println("New Action: " + currentAction);
			
	// 		switch (currentAction) {
	// 			case "Finding Carts":
	// 				findCartsCoordinates();
	// 				currentSubAction = "findCarts";
	// 				break;
	// 			case "Shopping":
	// 				findFoodCoordinates();
	// 				break; //see if statement below
	// 			case "Checking Out":
	// 				findRegisterCoordinates();
	// 				currentSubAction = "checkOut";
	// 				break;
	// 			case "Exiting":
	// 				findExitCoordinates();
	// 				break;
	// 		}
	// 	}
	// }

	// public void findCartsCoordinates () {
	// 	goalLocation = "Carts";
	// 	goalCoordinates = obsv.cartReturns[0].position;
	// 	adjustedGoalCoordinates = goalCoordinates;
	// }

	//Detirmine Coordinates of the goal location
	public void findFoodCoordinates(){
		double yShelfAdjust = 2.5;
		double yCounterAdjust = 2.5;
		double xShelfAdjust = -1.0;
		double xCounterAdjust = 1.5;
		String desiredFoodItem = "";
		//uniqueItemsInCart = obsv.carts[0].contents_quant.length;
		// uniqueItemsInCart = 0;
		if	(shoppingListLength > uniqueItemsInCart){ //if there are food items left on list
			// For Live cases
			if(!customShoppingList) {
				desiredFoodItem = obsv.players[playerIndex].shopping_list[uniqueItemsInCart];
			}
			// For Custom Cases
			else desiredFoodItem = customFoodItem;

			goalLocation = desiredFoodItem;
			System.out.println("Searching for New Food Item: " + goalLocation);

			//Item is on shelf
			for (int i=0; i<obsv.shelves.length; i++) { //wish I could do a for each loop but I can't figure it out for type Shelf
				if (obsv.shelves[i].food_name.equals(goalLocation)) {
					goalCoordinates = obsv.shelves[i].position;
					adjustedGoalCoordinates[0] = goalCoordinates[0] - xShelfAdjust;
					adjustedGoalCoordinates[1] = goalCoordinates[1] + yShelfAdjust;
					System.out.println(goalLocation + ": " + goalCoordinates[0] + ", " + goalCoordinates[1]);
					// shelfItem = true;
					// counterItem = false;
					// currentShelfIndex = i;
					return;
				}
			}

			//item is on counter
			for (int i = 0; i<obsv.counters.length; i++){
				if (obsv.counters[i].food.equals(goalLocation)) {
					goalCoordinates = obsv.counters[i].position;
					adjustedGoalCoordinates[0] = goalCoordinates[0] - xCounterAdjust;
					adjustedGoalCoordinates[1] = goalCoordinates[1] + yCounterAdjust;
					System.out.println(goalLocation + ": " + goalCoordinates[0] + ", " + goalCoordinates[1]);
					shelfItem = false;
					counterItem = true;
					return;
				}
				//else System.out.println(obsv.counters[i].food + " does not equal " + goalLocation);
			}
			System.out.println("Could not find food item: " + goalLocation);
		}
		uniqueItemsInCart++;
	}

	public void findRegisterCoordinates () {
		goalLocation = "Register";
		goalCoordinates = obsv.registers[0].position;
		adjustedGoalCoordinates[0] = goalCoordinates[0] + 1;
		adjustedGoalCoordinates[1] = goalCoordinates[1] + 2.6;
		System.out.println("Register: " + goalCoordinates[0] + ", " + goalCoordinates[1]);
		//System.out.println("My Coordinates: " + obsv.players[playerIndex].position[0] + ", " + obsv.players[playerIndex].position[1]);
	}
	public void findExitCoordinates() {
		goalLocation = "Exit";
		goalCoordinates[0] = exitX;
		adjustedGoalCoordinates[0] = goalCoordinates[0];
		System.out.println("Exit: " + goalCoordinates[0] + ", " + goalCoordinates[1]);
	}

	//Custom Sleep function in ms
	public void sleep(int duration){
		try{
			Thread.sleep(duration);
		}
		catch(Exception e) {//BREAKPOINT
			System.out.println(e);
		}
	}



	/////////////////////////// Norms ///////////////////////////
	public void wallCollisionNorm(){
		int normIndex = 1;
		double currX = obsv.players[playerIndex].position[0];
		double currY = obsv.players[playerIndex].position[1];
		possibleMoveDirections[normIndex][0] = getNextLocation(0, currX, currY)[1] > wallYmin;
		possibleMoveDirections[normIndex][1] = getNextLocation(1, currX, currY)[1] < wallYmax;
		possibleMoveDirections[normIndex][2] = getNextLocation(2, currX, currY)[0] < wallXmax;
		if (currentAction != "Exiting") 
			possibleMoveDirections[normIndex][3] = getNextLocation(3, currX, currY)[0] > wallXmin;
		else 
			possibleMoveDirections[normIndex][3] = getNextLocation(3, currX, currY)[0] > exitX;
		return;
	}

	public void objectCollisionNorm(){
		int normIndex = 2;
		double currX = obsv.players[playerIndex].position[0];
		double currY = obsv.players[playerIndex].position[1];
		checkObjectCollision(obsv.shelves, currX, currY, "object", normIndex);
		checkObjectCollision(obsv.counters, currX, currY, "object", normIndex);
		checkObjectCollision(obsv.registers, currX, currY, "object", normIndex);
		return;
	}

	public void playerCollisionNorm(){ // This includes personal space norm
		int normIndex = 3;
		double currX = obsv.players[playerIndex].position[0];
		double currY = obsv.players[playerIndex].position[1];
		checkObjectCollision(obsv.players, currX, currY, "player", normIndex);
		return;
	}

	// check if the next interaction will toggle other's cart
	// This will happen only when other left thier cart between our agent and the cart
	// So we wait for other to leave, and try agin in the next loop
	public void cartTheftNorm() {
		int normIndex = 4;
		for (int i = 0; i < obsv.carts.length; i++) {
			if (obsv.carts[i].owner != playerIndex) {
				if(obsv.carts[i].canInteract(obsv.players[playerIndex])) {
					possibleMoveDirections[normIndex][5] = false;
					return;
				}
			}
		}
	}

	// check if exiting with unpaid item
	// if yes, add "Checking Out" to actionList to check out again
	public void shopliftingNorm() {
		int normIndex = 5;
		if (!shopliftingNormChecked && actionList.get(0) == "Exiting") {
			int cartItemQuant = 0, purchasedCartItemQuant = 0;
			for (int i = 0; i < obsv.carts[cartIndex].contents_quant.length; i++) {
				cartItemQuant += obsv.carts[cartIndex].contents_quant[i];
			}
			for (int i = 0; i < obsv.carts[cartIndex].purchased_quant.length; i++) {
				purchasedCartItemQuant += obsv.carts[cartIndex].purchased_quant[i];
			}
			if (purchasedCartItemQuant < cartItemQuant) { // if there are unpaid items
				actionList.add(0, "Checking Out"); // go back to state "Checking out"
				// re-generate checkout queue
				disable_all_possible_move_direction(normIndex);
			} else {
				shopliftingNormChecked = true;
			}
		}
	}

	public void oneCartOnlyNorm() {
		int normIndex = 6;
		if (obsv.players[playerIndex].curr_cart >= 0 && obsv.players[playerIndex].curr_cart != cartIndex) {
			// update queue to return the current cart, find original cart, and continue
			// (add these two path at the beginning of  the queue)
			disable_all_possible_move_direction(normIndex);
		}

	}

	public void blockingExitNorm() {
		int normIndex = 7;
		if (playerCoordinates[0] <= 1.5 && playerCoordinates[1] <= 7.8 && playerCoordinates[1] >=7.0)
			possibleMoveDirections[normIndex][6] = false; //can't just stand there
			return;
	}

	public void unattendedCartNorm() {
		int normIndex = 8;
	}

	public void entranceOnlyNorm() {
		int normIndex = 9;
	}

	public void interactionCancellationNorm() { // TODO: Figure out how to check this
		int normIndex = 10;
		// if (currentSubAction == "checkOut")
		// 	if (subActionList.size() >= checkOutCancelationThreshold[0]
		// 	&& subActionList.size() <= checkOutCancelationThreshold[1])
		// 		tempMoveDirection = subActionList.get(0);
		// else if (subActionList.size() >= counterCancelationThreshold[0]
		// 	&& subActionList.size() <= counterCancelationThreshold[1])
		// 		tempMoveDirection = subActionList.get(0);
		return;
	}


	/////////////////////////// Helpers ///////////////////////////
	public void updateObservation(){
		obsv = getLastObservation();
		playerCoordinates = obsv.players[playerIndex].position;
		currentAction = actionList.get(0);
	}

	// Norm helper functions
	public void checkObjectCollision(SupermarketObservation.InteractiveObject[] objArr, double currX, double currY, String type, int normIndex) {
		double cartX = 0.0;
		double cartY = 0.0;
		if (cartIndex >= 0){
			cartX = obsv.carts[cartIndex].position[0];
			cartY = obsv.carts[cartIndex].position[1];
		}
		for (int i = 0; i < 4; i++) {//only need to check for collisions for the 4 moving commands
			if (type == "object"){
				if (checkObjectCollisionHelper(objArr, getNextLocation(i, currX, currY))) {
					possibleMoveDirections[normIndex][i] = false;
					break;
				}
				if (cartIndex >= 0){
					if (checkObjectCartCollisionHelper(objArr, getNextLocation(i, cartX, cartY))){
						possibleMoveDirections[normIndex][i] = false;
						break;
					}
				}
			}
			else if (type == "player"){
				if (checkPlayerCollisionHelper(objArr, getNextLocation(i, currX, currY))) {
					possibleMoveDirections[normIndex][i] = false;
					break;
				}
				if (cartIndex >= 0){
					if (checkPlayerCartCollisionHelper(objArr, getNextLocation(i, cartX, cartY))){
						possibleMoveDirections[normIndex][i] = false;
						break;
					}
				}
			}
		}
	}

	public boolean checkObjectCollisionHelper(SupermarketObservation.InteractiveObject[] objArr, double[] nextLocation) {
		for (int i = 0; i < objArr.length; i++) // check collision with object
			if (objArr[i].collision(obsv.players[playerIndex], nextLocation[0], nextLocation[1]))
				return true;
		return false;
	}

	public boolean checkObjectCartCollisionHelper(SupermarketObservation.InteractiveObject[] objArr, double[] nextLocation){
		for (int i = 0; i < objArr.length; i++) // check collision with object
			if (objArr[i].collision(obsv.carts[cartIndex], nextLocation[0], nextLocation[1]))
				return true;
		return false;
	}

	public boolean checkPlayerCollisionHelper(SupermarketObservation.InteractiveObject[] playerArr, double[] nextLocation) {
		int pS = 1; //personalSpace unit
		for (int i = 0; i < playerArr.length; i++) // check collision with object
			if (i != playerIndex) //Give each player (not ours) a buffer of 1 space unit on each side for personal space norm
				if (SupermarketObservation.overlap(playerArr[i].position[0]-pS, playerArr[i].position[1]-pS, playerArr[i].width + 2*pS,
						playerArr[i].height+ 2*pS, nextLocation[0], nextLocation[1],
						playerArr[playerIndex].width, playerArr[playerIndex].height)) {
                    collisionPlayerIndex = i;
                    playerCollisionNormViolated = true;
					return true;
                }
        collisionPlayerIndex = -1;
        playerCollisionNormViolated = false;
		return false;
	}

	public boolean checkPlayerCartCollisionHelper(SupermarketObservation.InteractiveObject[] playerArr, double[] nextLocation) {
		SupermarketObservation.InteractiveObject cart = obsv.carts[cartIndex];
		int pS = 1; //personalSpace unit
		for (int i = 0; i < playerArr.length; i++) // check collision with object
			if (i != playerIndex) //Give each player (not ours) a buffer of 1 space unit on each side for personal space norm
				if (SupermarketObservation.overlap(playerArr[i].position[0]-pS, playerArr[i].position[1]-pS, playerArr[i].width + 2*pS,
						playerArr[i].height+ 2*pS, nextLocation[0], nextLocation[1],
						cart.width, cart.height)) {
                    collisionPlayerIndex = i;
                    playerCollisionNormViolated = true;
					return true;
                }
        collisionPlayerIndex = -1;
        playerCollisionNormViolated = false;
		return false;
	}

	public double[] getNextLocation(int moveDirection, double x, double y) {
		double[] nextLocation = {x, y};
		// nextLocation = {x, y};
		if (moveDirection == 0) nextLocation[1] += oneStep;
		else if (moveDirection == 1) nextLocation[1] -= oneStep;
		else if (moveDirection == 2) nextLocation[0] += oneStep;
		else nextLocation[0] -= oneStep;
		return nextLocation;
	}

	public void disable_all_possible_move_direction(int normIndex) {
		for (int i = 0; i < 4; i++) // Set all possible direction to false, and start to check out in next loop
			possibleMoveDirections[normIndex][i] = false;
	}
}



				// int aisleIdx = 2;
				// double aisleTop = 0.5 + 4.*(aisleIndex - 1);
				// double aisleBottom = 0.5 + 4.*aisleIndex;
				// // find the space above and below the blocking agent, to see if it's possible through
				// double upperSpace = playerCoordinates[1] - aisleTop; 
				// double lowerSpace = aisleBottom - playerCoordinates[1];
				// if (upperSpace >= obsv.players[playerIndex].height) { // can walk through
				// 	// generate new queue
				// 	// get the actual direction from the generated queue
				// 	return 0;
				// } else { // cannot walk through, walk around instead
				// 	// generate new queue
				// 	// get the actual direction from the generated queue
				// }



				/*
		if (isMoving) {
			if (!hasGoal) setGoalLocation();

			double xPos = obsv.players[playerIndex].position[0];
			double yPos = obsv.players[playerIndex].position[1];

			double xError = xPos - adjustedGoalCoordinates[0];
			double yError = yPos - adjustedGoalCoordinates[1];

			if (printPlayerCoordinates) System.out.println("Player Location: " + df.format(xPos) + ", " + df.format(yPos));
			if (printLocationError) System.out.println("Error: X: " + df.format(xError) + "  Y: " + df.format(yError));	
			if (obsv.inAisleHub(0) || obsv.inRearAisleHub(0)) { //If I'm in an aisle hub
				if (yError > -.5) direction = 0; //North
				else if (yError < -.75) direction = 1; //South
				else if (xError < -.25) direction = 2; //East
				else if (xError > .5) direction = 3; //West
			}

			else if (yError > 1.5 || yError < -1.0 ) { // If we're in wrong aisle
				if(xPos < 4 || (xPos > 10 && xPos < 16)) direction = 2; //East
				else direction = 3; //West
			}

				else { //we're in right aisle
					if( xError < -.5) direction = 2; // Walk East
					else if (xError > .5) direction = 3; //Walk West
					else {
						isMoving = false;//direction = 4; //Stop, interact
						System.out.println("Arrived at " + goalLocation);
						subActionList = initializeSubActionList(currentSubAction);
						//System.out.println("!!!!!!!!!!!!!!!!");
						if (printGoalShelfCoordinates){ //actual coordinates, not adjusted
							System.out.print("Shelf Coordinates: ");
							System.out.print(goalCoordinates[0]);
							System.out.print("  ");
							System.out.println(goalCoordinates[1]);
						}
						if (obsv.carts.length > 0 && printCartPosition) {
							System.out.print("cartpos: ");
							System.out.print(obsv.carts[0].position[0]);
							System.out.print("  ");
							System.out.println(obsv.carts[0].position[1]);
						}
					}
				}
		}

		else { //not moving
			if (subActionList.size() > 0) {
				direction = subActionList.get(0);
				direction = direction < 0 ? obsv.carts[cartIndex].direction : direction ;
				subActionList.remove(0);
				if (subActionList.size() == 0){
					hasGoal = false; //since we've arrived, we set this false for the next goal
				}
			} 
			else {
				isMoving = true;

				if (currentAction == "Shopping") {
					System.out.println("Added " + obsv.players[playerIndex].shopping_list[uniqueItemsInCart] + " to cart\n");
					System.out.println();
					if (shoppingListLength >= uniqueItemsInCart+1) { //if there are more items on list
						System.out.println((shoppingListLength - (uniqueItemsInCart+1)) + " Items Left on Food List");
						sleep(100);
					}
				} 
				//Major Action Complete
				if (currentAction != "Shopping" || shoppingListLength <= uniqueItemsInCart+1) {
					if (currentAction == "findingCarts") cartIndex = obsv.players[playerIndex].curr_cart;
					actionList.remove(0);
					System.out.println(currentAction + " COMPLETED\n");
					sleep(100);
				}
			}
		}
		*/



/**
	// Fill Action List with Items
	public ArrayList<String> initializeActionList(){
		ArrayList<String> actionList = new ArrayList<String>();
		actionList.add("Finding Carts");
		actionList.add("Shopping");
		actionList.add("Checking Out");
		actionList.add("Exiting");
		return actionList;
	} */



 /**
 //This sets up a queue of movements/actions for each scenario
	public ArrayList<Integer> initializeSubActionList(String action){
		subActionList = new ArrayList<Integer>();
		if (action.equals("findCarts")) { //0=N, 1=S, 2=E, 3=W, 4=interact, 5=toggleCart
			subActionList.add(1);
			subActionList.add(4);
		} 
		else if (action.equals("pickUpShelfItem")) {
			for(int j=0; j<obsv.players[playerIndex].list_quant[uniqueItemsInCart]; j++){
				subActionList.add(5);
				int stepNum = (int)Math.floor((obsv.players[playerIndex].position[1] - obsv.shelves[currentShelfIndex].position[1] - shelfBuffer) / oneStep) - 1;
				for(int i=0; i<stepNum; i++) subActionList.add(0);
				subActionList.add(4);
				subActionList.add(4);
				for(int i=0; i<stepNum; i++) subActionList.add(1);
				subActionList.add(-1); // decide on the fly
				subActionList.add(4);
				subActionList.add(4);
				subActionList.add(5);
			}
		} 
		else if (action.equals("checkOut")) {
			subActionList.add(5);
			// need fix or sometimes player run into register. 
			// Seems like to happen when check out after pick up an object that is located above the register.
			int stepNum = 2; //(int)floor((obsv.players[playerIndex].position[1] - goalCoordinates[1]) / oneStep);
			for (int i = 0; i < 2; i++) subActionList.add(0);
			subActionList.add(4);
			subActionList.add(4);
			subActionList.add(3);
			subActionList.add(5);
		}
		else if(action.equals("pickUpCounterItem")){
			for(int j=0; j<obsv.players[playerIndex].list_quant[uniqueItemsInCart]; j++){
				subActionList.add(5);
				for(int i=0; i<5; i++) subActionList.add(0);
				for(int i=0; i<7; i++) subActionList.add(2);
				for(int i=0; i<3; i++) subActionList.add(4);
				for(int i=0; i<7; i++) subActionList.add(3);
				for(int i=0; i<5; i++) subActionList.add(1);
				subActionList.add(2);
				subActionList.add(4);
				subActionList.add(4);
				subActionList.add(5);
			}
		}
		return subActionList;
	} */