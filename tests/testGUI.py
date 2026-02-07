from Helpfulfunctions import multiple_select_window, TextinputWindow

functiontotest="TextinputWindow"
match functiontotest:
    case "multiple_select_window":
        print(f"You've selected {multiple_select_window("Choose a random combination",[1,2,3,4,5,6])}")
    case "TextinputWindow":
        print(f"You've entered {TextinputWindow("Gib einen Text ein")}")