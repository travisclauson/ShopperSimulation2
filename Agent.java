//README
// I couldn't figure out how to actually grab the items and put them in the cart
// For now, approaching a shelf is hacky, i just ram into it
// I initialize the shopping list myself at the bottom of this script (line 259)
// It should work for any food items except the back counters

import java.util.ArrayList;
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

	int moveDirection; //0=N, 1=S, 2=E, 3=W, 4=null
	int count = 0;
	double[] goalCoordinates = {0.0,0.0};
	String goalLocation = "";
	String currentAction = "";
	boolean setupDone = false;
	int uniqueItemsInCart = 0;
	ArrayList<String> actionList;
	boolean foundCoordinates = false;
	int shoppingListLength = 0;

	//print statements on/off
	boolean printPlayerLocation = false;
	boolean printGoalLocation = false;
	boolean printLoop = false;
	DecimalFormat df = new DecimalFormat("##.#");


	@Override
	protected void executionLoop() {
		if (!setupDone) setup();
		if (printLoop) System.out.println("Loop: " + Integer.toString(count));
		
		//SENSE
		obsv = getLastObservation();

		//DECIDE - where is the next goal, how do we get there, set moveDirection
		decide();

		//MOVE - move based on moveDirection
		move();

		count+=1;
	}

	//Prints Shopping and Action List
	public void setup(){ 
		obsv = getLastObservation();

		actionList = initializeActionList();
		System.out.println("Action List:");
		System.out.println(actionList);

		shoppingListLength = obsv.players[0].shopping_list.length;
		System.out.println("Shopping List:");
		for(int i=0; i<shoppingListLength; i++){
			System.out.println(
			String.valueOf(obsv.players[0].list_quant[i]) + " - " + 
			obsv.players[0].shopping_list[i]);
		}

		setupDone = true;
	}

	/////////// 2 CORE FUNCTIONS ///////////

	//Decide which direction to walk
	public void decide(){
		setGoalLocation();

		double yShoppingAdjust = 2.5;
		double xShoppingAdjust = -1.0;
		double xPos = obsv.players[0].position[0];
		double yPos = obsv.players[0].position[1];
		double xError = xPos - goalCoordinates[0];
		double yError = yPos - goalCoordinates[1];

		if (currentAction == "Shopping") {
			yError-=yShoppingAdjust;
			xError+=xShoppingAdjust;
		}

		if (printPlayerLocation) System.out.println("Player Location: " + df.format(xPos) + ", " + df.format(yPos));
		
		if(obsv.inAisleHub(0) || obsv.inRearAisleHub(0)) { //If I'm in an aisle hub
			if (yError > -.5) moveDirection = 0; //North
			else if (yError < -.75) moveDirection = 1; //South
			else if (xError < -.25) moveDirection = 2; //East
			else if (xError > .5) moveDirection = 3; //West
		}

		else if (yError > 1.5 || yError < -1.0 ) { // If we're in wrong aisle
			moveDirection = 2; //Walk West towards HUB
		}

		else { //we're in right aisle
			if( xError < -.5) moveDirection = 2; // Walk East
			else if (xError > .5) moveDirection = 3; //Walk West
			else moveDirection = 4; //Stop, interact
		}
		obsv.players[0].direction = 0;
	}
	
	//Literally just walk in the direction that Decide() detirmines, interact if neccesary
	public void move(){
		if (moveDirection == 0) goNorth();
		if (moveDirection == 1) goSouth(); 
		if (moveDirection == 2) goEast(); 
		if (moveDirection == 3) goWest();
		if (moveDirection == 4) {
			nop();
			arrivedAtItem();
		}
	}

	/////////// SECONDARY FUNCTIONS ///////////

	//Discover what our goal location is: exit, shelf x, register etc.
	public void setGoalLocation() {
		if (currentAction != actionList.get(0)) {
			String lastAction = currentAction;
			currentAction = actionList.get(0);
			System.out.println("New Action: " + currentAction);
			
			switch (currentAction){
				case "Finding Carts":
					findCartsCoordinates();
					break;
				case "Shopping":
					findFoodCoordinates();
					break;
				case "Checking Out":
					findRegisterCoordinates();
					break;
				case "Exiting":
					findExitCoordinates();
					break;
			}
		}
		// If we're shopping but need to look for a new item
		else if (currentAction == "Shopping" && goalLocation != obsv.players[0].shopping_list[uniqueItemsInCart]){ 
			findFoodCoordinates();
		}
	}

	public void findCartsCoordinates () {
		goalLocation = "Carts";
		goalCoordinates = obsv.cartReturns[0].position;
	}

	//Detirmine Coordinates of the goal location
	public void findFoodCoordinates(){
		uniqueItemsInCart = obsv.carts[0].contents_quant.length;
		if	(shoppingListLength > uniqueItemsInCart){ //if there are food items left on list
			String currItem;
			String desiredFoodItem =  obsv.players[0].shopping_list[uniqueItemsInCart];
			if  (!goalLocation.equals(desiredFoodItem)){ //If we're onto a new item, find coordinates
				goalLocation = desiredFoodItem;
				System.out.println("Searching for New Food Item: " + desiredFoodItem);
				for (int i=0; i<obsv.shelves.length; i++) { //wish I could do a for each loop but I can't figure it out for type Shelf
					currItem = obsv.shelves[i].food_name;
					if (currItem.equals(goalLocation)) {
						goalCoordinates = obsv.shelves[i].position;
						//System.out.println(goalLocation + ": " + goalCoordinates[0] + ", " + goalCoordinates[1]);
						foundCoordinates = true;
					}
				}
			}

		}
		else{
			actionList.remove(0);
		}
	}

	public void findRegisterCoordinates () {
		goalLocation = "Register";
		goalCoordinates = obsv.registers[0].position;
		goalCoordinates[1] += 2.75;
		//System.out.println("goal coordinates: " + goalCoordinates[0] + ", " + goalCoordinates[1]);
		//System.out.println("My Coordinates: " + obsv.players[0].position[0] + ", " + obsv.players[0].position[1]);
	}
	public void findExitCoordinates() { // This is a little hard-coded, only works at specific register
		goalLocation = "Exit";
		goalCoordinates[0] = -2;
	}

	 // Interact with object, then update new goal
	public void arrivedAtItem(){
		System.out.println("Arrived at " + goalLocation);
		foundCoordinates = false; //since we've arrived, we set this false for the next location
		
		switch(currentAction){
			case "Finding Carts":
				goSouth();
				interactWithObject();
				break;

			case "Shopping":
				if (shoppingListLength > uniqueItemsInCart) {
					pickUpFoodItem();
					System.out.println("Added " + obsv.players[0].shopping_list[uniqueItemsInCart] + " to cart");
					if (shoppingListLength != uniqueItemsInCart+1){ //if there are more items on list
						System.out.println((shoppingListLength - (uniqueItemsInCart+1)) + " Items Left on Food List");
						sleep(1000);
					}
				}
				break;

			case "Checking Out":
				checkOut();
				break;
		}

		if (currentAction != "Shopping" || shoppingListLength <= uniqueItemsInCart){
			actionList.remove(0);
			System.out.println(currentAction + " COMPLETED\n");
			sleep(1000);
		}
	}

	public void checkOut(){
		toggleShoppingCart();
		goNorth();
		goNorth();
		goNorth();
		interactWithObject();
		interactWithObject();
		interactWithObject();
		sleep(500);
		goWest();
		toggleShoppingCart();
	}

	//This is also hardcoded and is probably breaking the rules of one step per cycle
	public void pickUpFoodItem(){
		//System.out.println("Attempting to toggle shopping cart and move forward");
		toggleShoppingCart(); 
		for(int i=0; i<7; i++) goNorth();
		sleep(500);
		interactWithObject();
		interactWithObject();
		for(int i=0; i<7; i++) goSouth();
		moveDirection = obsv.carts[0].direction;
		move();
		interactWithObject();
		interactWithObject();
		toggleShoppingCart();
	}

	// Fill Action List with Items
	public ArrayList<String> initializeActionList(){
		ArrayList<String> actionList = new ArrayList<String>();
		actionList.add("Finding Carts");
		actionList.add("Shopping");
		actionList.add("Checking Out");
		actionList.add("Exiting");
		return actionList;
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
}


