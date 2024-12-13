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
    winning_combo: Vec<Cell>,
    play_count : i32,
}

impl Table{
    pub fn new() -> Table {
        let mut cells_in = (0..9).map(|i| Cell::new(String::new(), ' ', false, i, i, false)).collect();
        Table {
            cells: cells_in,
            full: false,
            winning_combo: Vec::new(),
            play_count: 0,
        }
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
        self.cells[index as usize].owner = player.name.clone();
        self.cells[index as usize].symbol = player.symbol.clone();
        self.cells[index as usize].is_occupied = true;
        self.print();
        self.play_count += 1;
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