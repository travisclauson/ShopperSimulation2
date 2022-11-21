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
	SupermarketObservation obsv;
	//int numShelves = obsv.shelves.length;
	int moveDirection; //0=N, 1=S, 2=E, 3=W, 4=null
	int count = 0;
	double[] goalCoordinates = {0.0,0.0};
	String goalLocation = "";
	String currentAction = "";
	boolean setupDone = false;
	int shoppingListLength = 0;
	int uniqueItemsInCart = 0;
	ArrayList<String> actionList;
	boolean foundGoalLocation = false;
	//print statements on/off
	boolean printPlayerLocation = false;
	boolean printGoalLocation = true;
	boolean printLoop = true;
	DecimalFormat df = new DecimalFormat("##.#");

	public Agent() {
		super();
		shouldRunExecutionLoop = true;
	}

	//intializes Food and action Lists
	public void setup(){ 
		obsv = getLastObservation();
		System.out.println("Shopping List:");
		shoppingListLength = obsv.players[0].shopping_list.length;
		for(int i=0; i<shoppingListLength; i++){
			System.out.println(
			String.valueOf(obsv.players[0].list_quant[i]) + " - " + 
			obsv.players[0].shopping_list[i]);
		}
		actionList = initializeActionList();
		System.out.println(actionList);
		setupDone = true;
		System.out.println("Setup Done");
	}

	@Override
	protected void executionLoop() {
		if (!setupDone) setup();
		if (printLoop) System.out.println("Loop: " + Integer.toString(count)); //Print loop number if set above
		sense(); //sense the situtation, set the goal
		decide(obsv); //detirmines next movement direction
		act(obsv); //moves
		count+=1;
	}

	//Finds the coordinates of the desired location
	public void sense(){ //
		obsv = getLastObservation();
		while(true){
			System.out.println("looping Sense");
			setGoalLocation(obsv);
			if (printGoalLocation) System.out.println("Goal Location: " + goalLocation);
			if( goalLocation != "") break; //try again if goalLocation is empty
		}
	}

	//Decide which direction to walk
	public void decide(SupermarketObservation obsv){
		double yShoppingAdjust = 2.5;
		double xPos = obsv.players[0].position[0];
		double yPos = obsv.players[0].position[1];
		double xError = xPos - goalCoordinates[0];
		double yError = yPos - goalCoordinates[1];
		if (currentAction == "Shopping") yError-=yShoppingAdjust;
		//if (printPlayerLocation) System.out.println("Player Location: " + df.format(xPos) + ", " + df.format(yPos));
		if(obsv.inAisleHub(0) || obsv.inRearAisleHub(0)) { //If I'm in an aisle hub
			if (yError > .5) {moveDirection = 0; //North
				//System.out.println("YError: " + yError);
			}
			else if (yError < -.25) {moveDirection = 1; //South
				//System.out.println("YError: " + yError);
			}
			else if (xError < -.25) moveDirection = 2; //East
			else if (xError > .5) moveDirection = 3; //West
		}
		else if (yError > 1.5 || yError < -.5 ) { // If we're in wrong aisle
			moveDirection = 2; //Walk West towards HUB
		}
		else { //we must be in right aisle
			if( xError < -.5) moveDirection = 2; // Walk East
			else if (xError > .5) moveDirection = 3; //Walk West
			else moveDirection = 4; //Stop, interact
		}
		obsv.players[0].direction = 0;
	}
	
	//Literally just walk in the direction that Decide() detirmines, interact if neccesary
	public void act(SupermarketObservation obsv){
		if (moveDirection == 0) goNorth();
		if (moveDirection == 1) goSouth(); 
		if (moveDirection == 2) goEast(); 
		if (moveDirection == 3) goWest();
		if (moveDirection == 4) {
			nop();
			arrivedAtItem(obsv);
		}
	}

	//Discover what our goal location is: exit, shelf x, register etc.
	public void setGoalLocation(SupermarketObservation obsv) {
		if (currentAction != actionList.get(0)) {
			String lastAction = currentAction;
			currentAction = actionList.get(0);
			System.out.println("New Action: " + currentAction);
			switch (currentAction){
				case "Finding Carts":
					findCartsCoordinates(obsv);
					break;
				case "Shopping":
					uniqueItemsInCart = obsv.carts[0].contents_quant.length;
					findFoodCoordinates(obsv);
					break;
				case "Checking Out":
					findRegisterCoordinates(obsv);
					break;
				case "Exiting":
					findExitCoordinates(obsv);
					break;
			}
		}
		// If we're shopping but need to look for a new item
		else if (currentAction == "Shopping" && goalLocation != obsv.players[0].shopping_list[obsv.carts[0].contents_quant.length]){ 
			findFoodCoordinates(obsv);
		}
	}

	//Detirmine Coordinates of the goal location
	public void findFoodCoordinates(SupermarketObservation obsv){
		if	(shoppingListLength>uniqueItemsInCart){ //if there are food items left on list
			String currItem;
			String desiredFoodItem =  obsv.players[0].shopping_list[uniqueItemsInCart];
			if  (goalLocation != desiredFoodItem){ //If we're onto a new item, find coordinates
				goalLocation = desiredFoodItem;
				System.out.println("Searching for New Food Item: " + desiredFoodItem);
				for (int i=0; i<obsv.shelves.length; i++) { //wish I could do a for each loop but I can't figure it out for type Shelf
					currItem = obsv.shelves[i].food_name;
					//System.out.println(currItem); //prints all items on shelves
					if (currItem.equals(goalLocation)) {
						goalCoordinates = obsv.shelves[i].position;
						//System.out.println(goalLocation + ": " + goalCoordinates[0] + ", " + goalCoordinates[1]);
						foundGoalLocation = true;
					}
				}
			}

		}
		else {
			actionList.remove(0);
		}
	}

	public void findCartsCoordinates (SupermarketObservation obsv) {
		goalLocation = "Carts";
		goalCoordinates = obsv.cartReturns[0].position;
		goalCoordinates[1] += -.5;
		//System.out.println("Cart Return Location: " + goalCoordinates);
	}
	public void findRegisterCoordinates (SupermarketObservation obsv) {
		goalLocation = "Register";
		goalCoordinates = obsv.registers[0].position;
		goalCoordinates[1] += 2.75;
		//System.out.println("goal coordinates: " + goalCoordinates[0] + ", " + goalCoordinates[1]);
		//System.out.println("My Coordinates: " + obsv.players[0].position[0] + ", " + obsv.players[0].position[1]);
	}
	public void findExitCoordinates(SupermarketObservation obsv) { // This is a little hard-coded, only works at specific register
		goalLocation = "Exit";
		goalCoordinates[0] = -2;
	}

	 // Interact with object, then update new goal
	public void arrivedAtItem(SupermarketObservation obsv){
		System.out.println("Arrived at " + goalLocation);
		//interact with object
		foundGoalLocation = false; //since we've arrived, we set this false for the next location
		//SupermarketObservation.CartReturn c = obsv.cartReturns[0];
		//SupermarketObservation.Player p = obsv.players[0];
		//while(SupermarketObservation.defaultCanInteract(c, p) == false){
		//}
		if (currentAction == "Finding Carts") {
			goSouth();
			interactWithObject();
			interactWithObject();
		}

		if (currentAction == "Shopping"){ //more hacky 2am fix!
			pickUpFoodItem(obsv);
			System.out.println("Added " + obsv.players[0].shopping_list[uniqueItemsInCart] + " to cart");
			if (shoppingListLength != uniqueItemsInCart){ //and if there are more items on list
				System.out.println((shoppingListLength - uniqueItemsInCart) + " Items Left on Food List");
				sleep(1000);
			}
		}
		if (currentAction == "Checking Out") { //Not sure why paying won't work
			checkOut();
		}
		if (currentAction != "Shopping" || shoppingListLength == uniqueItemsInCart) { //If we're done with our Action, move to next
			System.out.println("Action: " + currentAction + " completed");
			actionList.remove(0);
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
	public void pickUpFoodItem(SupermarketObservation obsv){
		//System.out.println("Attempting to toggle shopping cart and move forward");
		toggleShoppingCart(); 
		for(int i=0; i<7; i++) goNorth();
		sleep(500);
		System.out.println("Attempting to grab food");
		interactWithObject();
		interactWithObject();
		for(int i=0; i<7; i++) goSouth();
		moveDirection = obsv.carts[0].direction;
		act(obsv);
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


