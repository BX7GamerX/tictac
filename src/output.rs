use rand::Rng;
use std::io::Write;

pub struct Cell {
    pub owner: String,
    pub symbol: char,
    pub is_occupied: bool,
    pub index: i32,
    pub position: i32,
    pub winning_cell: bool,
    pub owner_id: i32,
}

impl Cell {
    fn new(
        owner: String,
        symbol: char,
        is_occupied: bool,
        index: i32,
        position: i32,
        winning_cell: bool,
        owner_id: i32,
    ) -> Cell {
        Cell {
            owner,
            symbol,
            is_occupied,
            index,
            position,
            winning_cell,
            owner_id,
        }
    }
}
pub fn position_to_index(position: i32) -> i32 {
    if position > 6 {
        return position - 7;
    } else if position > 3 {
        return position - 1;
    } else {
        return position + 5;
    }
}
pub struct Table {
    cells: Vec<Cell>,
    full: bool,
    //winning_combo: Vec<Cell>,
    play_count: i32,
    winning_combo: [[usize; 3]; 8],
    winner: String,
}

/// Creates a new `Table` instance with default values.

/// Returns the list of winning combinations that include the given cell index.

/// Checks if the given player has won after making a move at the specified index.

/// Initializes the `Table` for a new game.

/// Retrieves a reference to the `Cell` at the specified index.

/// Clears the console and prints the current state of the table.

/// Processes a player's move at the specified index.

/// Checks if the table is full (i.e., no more moves can be made).
impl Table {
    pub fn new() -> Table {
        let mut cells_in = (0..9)
            .map(|i| Cell::new(String::new(), ' ', false, i, i, false, 0))
            .collect();
        Table {
            cells: cells_in,
            full: false,
            winning_combo: [
                [0, 1, 2],
                [3, 4, 5],
                [6, 7, 8],
                [0, 3, 6],
                [1, 4, 7],
                [2, 5, 8],
                [0, 4, 8],
                [2, 4, 6],
            ],
            play_count: 0,
            winner: String::new(),
        }
    }
    fn get_relevant_list(&self, index: i32) -> Vec<[usize; 3]> {
        let mut relevant_list = Vec::new();
        for combo in self.winning_combo.iter() {
            if combo.contains(&(index as usize)) {
                relevant_list.push(*combo);
            }
        }
        relevant_list
    }
    fn check_winner(&mut self, player: &Player, index: i32) -> bool {
        for combo in self.get_relevant_list(index) {
            let mut count = 0;
            for cell in combo.iter() {
                if self.cells[*cell].owner == player.name {
                    count += 1;
                }
            }
            if count == 3 {
                for cell in combo.iter() {
                    self.cells[*cell].winning_cell = true;
                }
                return true;
            }
        }
        false
    }
    pub fn init(&mut self) {
        let mut count = 0;
        let mut position = 7;
        let mut row_count = 0;
        for cell in self.cells.iter_mut() {
            cell.owner = String::new();
            cell.symbol = count.to_string().chars().next().unwrap();
            cell.is_occupied = false;
            cell.winning_cell = false;
            cell.position = position;
            cell.index = count;
            position += 1;
            count += 1;
            row_count += 1;
            if row_count == 3 {
                row_count = 0;
                position -= 6;
            }
        }
    }
    pub fn get_cell(&self, index: i32) -> &Cell {
        &self.cells[index as usize]
    }

    pub fn print(&self) {
        if cfg!(target_os = "windows") {
            std::process::Command::new("cmd")
                .args(&["/C", "cls"])
                .status()
                .unwrap();
        } else {
            std::process::Command::new("clear").status().unwrap();
        }
        println!(
            "{} | {} | {}",
            self.symbol_or_position(0),
            self.symbol_or_position(1),
            self.symbol_or_position(2)
        );
        println!("---------");
        println!(
            "{} | {} | {}",
            self.symbol_or_position(3),
            self.symbol_or_position(4),
            self.symbol_or_position(5)
        );
        println!("---------");
        println!(
            "{} | {} | {}",
            self.symbol_or_position(6),
            self.symbol_or_position(7),
            self.symbol_or_position(8)
        );
    }
    fn symbol_or_position(&self, index: i32) -> String {
        if self.cells[index as usize].is_occupied {
            return self.cells[index as usize].symbol.to_string();
        }
        return self.cells[index as usize].position.to_string();
    }
    pub fn play(&mut self, player: &mut Player, index: i32) {
        if self.cells[index as usize].is_occupied {
            println!("Cell is already occupied");
            return;
        }
        if self.check_full() {
            return;
        };

        self.place_cell(player, index.clone());
        self.save_table_csv();
    }
    fn place_cell(&mut self, player: &mut Player, index: i32) {
        self.cells[index as usize].owner = player.name.clone();
        self.cells[index as usize].symbol = player.symbol.clone();
        self.cells[index as usize].is_occupied = true;
        self.cells[index as usize].owner_id = if player.name == "ai" { 1 } else { -1 };
        self.print();
        self.play_count += 1;
        if self.check_winner(player, index) {
            println!("{} wins!", player.name.clone());
            self.winner = player.name.clone();
            //self.save_table_csv();
            self.full = true;
        };
    }
    pub fn check_full(&mut self) -> bool {
        if self.play_count > 8 {
            self.full = true;
        }
        self.full
    }
    pub fn save_table_csv(&self) {
        let mut csv = String::new();
        csv.push_str("\n");
        for cell in self.cells.iter() {
            csv.push_str(&cell.owner_id.to_string());
            csv.push_str(",");
        }
        csv.push_str(&self.winner);

        std::fs::OpenOptions::new()
            .create(true)
            .append(true)
            .open("table.csv")
            .unwrap()
            .write_all(csv.as_bytes())
            .unwrap();

    }
}

pub struct Player {
    pub name: String,
    pub symbol: char,
    pub is_ai: bool,
    pub previous_moves: Vec<i32>,
}

impl Player {
    pub fn new(name: String, symbol: char) -> Player {
        let is_ai = if (name == "ai" || name == "ai_2") { true } else { false };
        Player {
            name,
            symbol,
            is_ai,
            previous_moves: Vec::new(),
        }
    }
    pub fn play(&mut self, table: &mut Table, index: i32) {
        table.play(self, position_to_index(index));
        self.previous_moves.push(index);
    }
}

pub fn get_int(message: &str) -> i32 {
    loop {
        println!("{}", message);
        let mut input = String::new();
        std::io::stdin().read_line(&mut input).unwrap();
        match input.trim().parse::<i32>() {
            Ok(num) => return num,
            Err(_) => println!("Invalid input"),
        }
    }
}
fn get_string(message: &str) -> String {
    loop {
        println!("{}", message);
        let mut input = String::new();
        std::io::stdin().read_line(&mut input).unwrap();
        let input = input.trim().to_string();
        if input.is_empty() {
            println!("Invalid input");
        } else {
            return input;
        }
    }
}
fn get_char(message: &str) -> char {
    loop {
        println!("{}", message);
        let mut input = String::new();
        std::io::stdin().read_line(&mut input).unwrap();
        let input = input.trim().to_string();
        if input.is_empty() || input.chars().count() > 1 {
            println!("Invalid input");
        } else {
            return input.chars().next().unwrap();
        }
    }
}
pub struct Game {
    pub tictac_board: Table,
    pub player1: Player,
    pub player2: Player,
    pub player1_moves: Vec<i32>,
    pub player2_moves: Vec<i32>,
}

impl Game {
    pub fn new(player_type:String) -> Game {
        let mut tictac_board = Table::new();
        tictac_board.init();
        let (player1, player2) = Game::init_player(player_type);
        Game {
            tictac_board,
            player1,
            player2,
            player1_moves: Vec::new(),
            player2_moves: Vec::new(),
        }
    }
    //initialize the players based oin the game type the user insrtucts
    pub fn init_player(player_type:String)->(Player,Player){
        if player_type == "ai_Vs_ai" {
            let player1 = Player::new("ai".to_string(), 'X');
            let player2 = Player::new("ai_2".to_string(), 'O');
            (player1, player2)
        } else if player_type == "human_Vs_human" {
            let player1 = Player::new(
                get_string("Enter player 1 name"),
                get_char("Choose symbol for player 1"),
            );
            let player2 = Player::new(
                get_string("Enter Player two name"),
                get_char("Choose symbol for player 2"),
            );
            (player1, player2)
        }
        else {
            let player1 = Player::new("ai".to_string(), get_char("Choose symbol for 'ai' :"));
            let player2 = Player::new(
                get_string("Enter player 2 name"),
                get_char("Choose symbol for player 2"),
            );
            (player1, player2)
        }
    }
    pub fn ai_play_move(&mut self) -> i32 {
        let mut rng = rand::thread_rng();
        let mut ai_move = rng.gen_range(1..10);
        while self.player1_moves.contains(&ai_move) || self.player2_moves.contains(&ai_move) {
            ai_move = rng.gen_range(1..10);
        }
        ai_move
    }
    pub fn play(&mut self) {
        let mut iterator = 0;
        self.tictac_board.print();
        loop {
            let input = self.get_input();
            if iterator == 0 {
                self.player1.play(&mut self.tictac_board, input);
                self.player1_moves.push(input);
            } else {
                self.player2.play(&mut self.tictac_board, input);
                self.player2_moves.push(input);
            }

            if self.tictac_board.check_full() {
                break;
            }

            iterator = if iterator == 0 { 1 } else { 0 };
        }
    }
    fn get_input (&mut self)-> i32 {
        let mut  input = 0;
        if (self.player1.is_ai) || (self.player2.is_ai) {
            let ai_move = self.ai_play_move();
            input = ai_move;
        } else {
            input = get_int("Enter a number between 1 and 9")
        };
        input
    }
}
