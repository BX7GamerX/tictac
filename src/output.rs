use rand::Rng;

pub struct Cell {
    pub owner: String,
    pub symbol: char,
    pub is_occupied: bool,
    pub index: i32,
    pub position: i32,
    winning_cell: bool,
}

impl Cell {
    fn new(owner: String, symbol: char, is_occupied: bool, index: i32, position: i32, winning_cell: bool) -> Cell {
        Cell {
            owner,
            symbol,
            is_occupied,
            index,
            position,
            winning_cell,
        }
    }
}
pub fn position_to_index(position: i32) -> i32 {
    if position > 6 {
        return position - 7;
    }else if position > 3 {
        return position - 1;
    }else {
        return position + 5;
    }
}
pub struct Table{
    cells: Vec<Cell>,
    full : bool,
    //winning_combo: Vec<Cell>,
    play_count : i32,
    winning_combo: [[usize;3]; 8],
}

/// Creates a new `Table` instance with default values.

/// Returns the list of winning combinations that include the given cell index.

/// Checks if the given player has won after making a move at the specified index.

/// Initializes the `Table` for a new game.

/// Retrieves a reference to the `Cell` at the specified index.

/// Clears the console and prints the current state of the table.

/// Processes a player's move at the specified index.

/// Checks if the table is full (i.e., no more moves can be made).
impl Table{
    pub fn new() -> Table {
        let mut cells_in = (0..9).map(|i| Cell::new(String::new(), ' ', false, i, i, false)).collect();
        Table {
            cells: cells_in,
            full: false,
            winning_combo : [
                [0,1,2],
                [3,4,5],
                [6,7,8],
                [0,3,6],
                [1,4,7],
                [2,5,8],
                [0,4,8],
                [2,4,6],
            ],
            play_count: 0,
        }
    }
    fn get_relevant_list (&self, index : i32 ) -> Vec<[usize;3]>{
        let mut relevant_list = Vec::new();
        for combo in self.winning_combo.iter(){
            if combo.contains(&(index as usize)){
                relevant_list.push(*combo);
            }
        }
        relevant_list
    }
    fn check_winner(&mut self, player: &Player , index : i32) -> bool {
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
    pub fn init (&mut self){
        let mut count = 0;
        let mut position = 7;
        let mut row_count = 0;
        for cell in self.cells.iter_mut(){
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
    pub fn get_cell (&self, index: i32) -> &Cell {
        &self.cells[index as usize]
    }
    
    pub fn print (&self){
        if cfg!(target_os = "windows") {
            std::process::Command::new("cmd")
                .args(&["/C", "cls"])
                .status()
                .unwrap();
        } else {
            std::process::Command::new("clear")
                .status()
                .unwrap();
        }
        println!("{} | {} | {}", self.cells[0].symbol, self.cells[1].symbol, self.cells[2].symbol);
        println!("---------");
        println!("{} | {} | {}", self.cells[3].symbol, self.cells[4].symbol, self.cells[5].symbol);
        println!("---------");
        println!("{} | {} | {}", self.cells[6].symbol, self.cells[7].symbol, self.cells[8].symbol);
    }
    pub fn play (&mut self, player: &mut Player, index: i32){
        if self.cells[index as usize].is_occupied {
            println!("Cell is already occupied");
            return;
        }
        if self.check_full(){
            return;
        };

        self.place_cell(player, index);

    }
    fn place_cell (&mut self, player: &mut Player, index: i32){

        self.cells[index as usize].owner = player.name.clone();
        self.cells[index as usize].symbol = player.symbol.clone();
        self.cells[index as usize].is_occupied = true;
        self.print();
        self.play_count += 1;
        if self.check_winner(player, index){
            println!("{} wins!", player.name);
            self.full = true;
        };
    }
    pub fn check_full (&mut self) -> bool{
        if self.play_count > 8 {
            self.full = true;
        }
        self.full
    }
}

pub struct  Player{
    pub name: String,
    pub symbol: char,
    pub is_ai: bool,
    pub previous_moves: Vec<i32>,
}

impl Player{
    pub fn new(name: String, symbol: char) -> Player {
        let is_ai = if name == "ai" { true } else { false };
        Player {
            name,
            symbol,
            is_ai,
            previous_moves: Vec::new(),
        }
    }
    pub fn play(&mut self, table: &mut Table, index: i32){
        table.play(self,position_to_index(index) );
        self.previous_moves.push(index);
    }
}

pub fn get_int (message: &str) -> i32 {
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
fn  get_string (message: &str) -> String {
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
fn get_char (message: &str) -> char {
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
    pub fn new() -> Game {
        let mut tictac_board = Table::new();
        tictac_board.init();
        let mut player1 = Player::new(
            get_string("Enter player 1 name"), 
            get_char("Choose symbol for player 1"),);
        let mut player2 = Player::new(
            get_string("Enter Player two name"), 
            get_char("Choose symbol for player 2"),);
        Game {
            tictac_board,
            player1,
            player2,
            player1_moves: Vec::new(),
            player2_moves: Vec::new(),
        }
    }
    pub fn ai_play_move(&mut self)-> i32{
        let mut rng = rand::thread_rng();
        let mut ai_move = rng.gen_range(1..10);
        while self.player1_moves.contains(&ai_move) || self.player2_moves.contains(&ai_move) {
            ai_move = rng.gen_range(1..10);
        }
        ai_move

    }
    pub fn play(&mut self){
        let mut iterator = 0;
        loop {
            let input = if (iterator == 0 && self.player1.is_ai) || (iterator == 1 && self.player2.is_ai) {
                let ai_move = self.ai_play_move();
                ai_move
            } else {
                get_int("Enter a number between 1 and 9")
            };

            if iterator == 0 {
                self.player1.play(&mut self.tictac_board, input);
                self.player1_moves.push(input);
            } else {
                self.player2.play(&mut self.tictac_board, input);
                self.player2_moves.push(input);
            }

            if self.tictac_board.check_full() {
                    println!("It's a draw!");
                
                break;
            }

            iterator = if iterator == 0 { 1 } else { 0 };
        }
    }
}

