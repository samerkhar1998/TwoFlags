import PySimpleGUI as sg

class startApp():

    def __init__(self):
        self.playerOne = True
        self.playerTwo = True
        self.Ip = '127.0.0.1'
        self.Port = 65432
        self.Online = False
        self.time = 5
        self.setup = "Setup Ba7 Bb7 Bc7 Bd7 Be7 Bf7 Bg7 Bh7 Wa2 Wb2 Wc2 Wd2 We2 Wf2 Wg2 Wh2"

    def Begin(self):
        layout = [[sg.Text("Play Offline", size=(40, 1), font=('Any 15'))],
                  [sg.Text("White Player"), sg.Button("Agent "), sg.Button("Human ")],
                  [sg.Text("Black Player"), sg.Button("agent"), sg.Button("human")],
                  [sg.Text("Time of the game is 5 minutes by default")],
                  [sg.Text("Enter time: "), sg.InputText(size=5)],
                  [sg.Text("You can setup the board before you start: ", font=('Any 12'))],
                  [sg.Text("Order of setup: Color of Pawn, file on board, number of row")],
                  [sg.Text("rows = 1-8, files a-h")],
                  [sg.Text("example of setup: Wb4 Wa3 Wc2 Bg7 Wd4 Bg6 Be7")],
                  [sg.Text("Enter setup: "), sg.InputText()],
                  [sg.Button("Start")],
                  [sg.HSeparator()],
                  [sg.Text("Agent Vs Server", size=(40, 1), font=('Any 15'))], [sg.Text("Ip"), sg.InputText(size=20)],
                  [sg.Text("Port"), sg.InputText(size=20)],
                  [sg.Button("Connect to server")],
                  ]

        # Create the window
        window = sg.Window("Flags Game", layout)

        # Create an event loop
        while True:
            event, values = window.read()
            # End program if user closes window or
            # presses the OK button
            if event == sg.WIN_CLOSED:
                break
            if event == "Agent ":
                self.playerOne = False
            if event == "Human ":
                self.playerOne = True
            if event == "agent":
                self.playerTwo = False
            if event == "human":
                self.playerTwo = True
            if event == "Start":
                if not values[0] == '':
                    self.time = int(values[0])
                if not values[1] == '':
                    self.setup = values[1]
                break
            if event == "Connect to server":
                self.Online = True
                if values[3] != '':
                    self.Ip = values[3]
                if values[4] != '':
                    self.Port = int(values[4])

                break

        window.close()






