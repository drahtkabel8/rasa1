from typing import Any, Text, Dict, List

from rasa_sdk import Action, Tracker
from rasa_sdk.events import SlotSet
from rasa_sdk.executor import CollectingDispatcher

look_descriptions = {
    "window": "A huge window with curtains on either side of it. They look expensive.",
    "terminal": "That's the terminal. The admin account is password protected.",
    "key": "A small golden key.",
    "door": "The door fell shut behind me when I entered the room. I'm a dumbass and forgot to check for a key or doorstopper and of course it locks when it shuts, so basically I'm stuck in here.",
    "curtains": "Those curtains are made from thick, high quality fabric. Naturally. Gotta stop the outside from peeking in... Or the inside from peeking out.",
    "room": "The room is kinda plain. There's a window across from the door, a desk, and a terminal on top of it.",
    "printer": "It's a high-end printer.",
    "drawer": "A drawer with a small lock. I can't open it without a key.",
    "desk": "A desk with a printer and a terminal on it. There's a drawer on the side.",
    "documents": "Some pretty interesting documents. I can't take them with me if I don't want to get caught, but perhaps the files are still on the terminal..."
}


able_to_pick_up = ["key", "curtains"]


class ActionLook(Action):
    def name(self) -> Text:
        return "action_look"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        spoken = False
        for blob in tracker.latest_message['entities']:
            if blob['entity'] == 'object':
                dispatcher.utter_message(text=look_descriptions[blob['value']])
                spoken = True
        if not spoken:
            dispatcher.utter_message(text="I can't seem to see anything like that in here.")
        return []


# class ActionCheckSlot(Action):
  #  def name(self) -> Text:
   #     return "action_slot"

    #def run(self, dispatcher: CollectingDispatcher,
     #       tracker: Tracker,
      #      domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
       #     bool1 = tracker.get_slot('key')
        #    if bool1 == True:
                
        #return [] 


class ActionPickUp(Action):
    def name(self) -> Text:
        return "action_pickup"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        items_to_add = []
        # We need to check what objects the user wants to pick up. We cannot pick up
        # all objects and we need to check if the object is already in your inventory.
        for blob in tracker.latest_message['entities']:
            if blob['entity'] == 'object':
                item = blob['value']
                if item not in able_to_pick_up:
                    dispatcher.utter_message(text=f"Why and how would I pick up the {item}? I can't do that.")
                else:
                    item_in_inventory = tracker.get_slot(item)
                    if item_in_inventory:
                        dispatcher.utter_message(text=f"I already picked up the {item}.")
                    else:
                        items_to_add.append(SlotSet(item, True))
                        dispatcher.utter_message(text=f"Alright, picked the {item} up. What next?")

        # We could add multiple items here.
        if len(items_to_add) > 0:
            return items_to_add
        dispatcher.utter_message(text="Are you sure you spelled that right? What do you want me to pick up?")
        return []


class ActionInventory(Action):
    def name(self) -> Text:
        return "action_inventory"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        items_in_inventory = [item for item in able_to_pick_up if tracker.get_slot(item)]
        if len(items_in_inventory) == 0:
            dispatcher.utter_message(text="I'm not carrying anything right now, chief.")
            return []
        dispatcher.utter_message(text="Right now, I'm carrying:")
        for item in items_in_inventory:
            dispatcher.utter_message(text=f"- {item}")
        return []


combinations = {
    ('key', 'door'): "That doesn't fit. The key is too small for the door lock. Maybe there's another lock in the room?",
    ('key', 'window'): "Even if that key worked for the window - which it doesn't, for the record - I wouldn't jump outta there. We're on the 3rd floor, I could break something. Would be convenient if I had a ladder...",
    ('curtains', 'window'): "Honestly? That's insane. But it just might work out. [ Per ties the curtains together, attaches one of them to the curtain bar, and starts climbing down. ] Congrats! You've solved the level.",
    ('key', 'drawer'): "[ The lock clicks and the drawer opens. Inside is a stack of documents. ] ...Nice.",
    ('key', 'printer'): "How is that supposed to work?",
    ('documents', 'printer'): "It's a printer, not a scanner. It's connected to the terminal.",
    ('terminal', 'password'): "[ Per enters the password and the terminal grants access. ] Hell yeah. There's an important document with a good few pages of sensitive information on here. If only there was a way to take them with me...",
    ('terminal', 'printer'): "[ the printer starts reproducing the documents from the drawer. ] Sweet. That's it. Let's take these and get me outta here.'"
}


combinations.update({(i2, i1): v for (i1, i2), v in combinations.items()})


class ActionUse(Action):
    def name(self) -> Text:
        return "action_use"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        entities = [e['value'] for e in tracker.latest_message['entities'] if e['entity'] == 'object']
        if len(entities) == 0:
            dispatcher.utter_message(text="I think you want me to combine some items, but I don't really get which two.")
            dispatcher.utter_message(text="I'm pretty sure you're misspelling something. Could you try again?")
            return []
        elif len(entities) == 1:
            dispatcher.utter_message(text="I think you want me to combine some items, but I don't really get which two.")
            dispatcher.utter_message(text=f"I need a second item to use with {entities[0]}.")
            dispatcher.utter_message(text="Any other ideas?")
            return []
        elif len(entities) > 2:
            dispatcher.utter_message(text="I think you want me to combine some items, but I don't really get which two.")
            dispatcher.utter_message(text=f"I could only make out that you wanted me to combine {' and '.join(entities)}.")
            dispatcher.utter_message(text="I can only combine two items at a time. I only have two hands, bro...")
            return []
        # there are two items and they are confirmed
        item1, item2 = entities
        if (item1, item2) in combinations.keys():
            dispatcher.utter_message(text=combinations[(item1, item2)])
        else:
            dispatcher.utter_message(text=f"I don't think combining the {item1} with the {item2} makes a lot of sense.")
        return []

