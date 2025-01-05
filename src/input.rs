use csv::ReaderBuilder;
use std::{error::Error, string};

#[derive(Clone)]
pub struct GameData {
    pub winner: String,
    pub player1: String,
    pub player2: String,
    pub state_of_cells_list: Vec<[i8;9]>,
    pub periodic_state_of_cells : [i8;9],
}
impl GameData {
    pub fn new(player1: String, player2: String) -> GameData {
        GameData {
            winner : String::from(""),
            player1,
            player2,
            state_of_cells_list : Vec::new(),
            periodic_state_of_cells: [0;9],
        }
    }
    pub fn get_round_State (&self, index: usize) -> [i8;9] {
        if index >= self.state_of_cells_list.len() {
            return self.state_of_cells_list[self.state_of_cells_list.len()-1];
        }
        self.state_of_cells_list[index]
    }
}

pub struct GamesData {
    pub game_data: Vec<GameData>,
    pub csv_file: String,

}
impl GamesData {
    pub fn new(csv_file: String) -> GamesData {
        GamesData {
            csv_file,
            game_data: Vec::new(),
        }
    }
    pub fn add_game(&mut self, game_data: GameData) {
        self.game_data.push(game_data);
    }
    pub fn get_game(&self, index: usize) -> GameData {
        self.game_data[index].clone()
    }
    pub fn print_game(&self, index: usize) {
        let game = self.get_game(index);
        println!("Winner: {}", game.winner);
        println!("Player 1: {}", game.player1);
        println!("Player 2: {}", game.player2);
        println!("---------------------------------");
        for state in game.state_of_cells_list.iter(){
            for cell in state.iter(){
                print!("{} ", cell);
            }
            println!();
        }
    }
    // the glory code please don't touch it
    pub fn read_data(&mut self) {
        let reader = ReaderBuilder::new()
            .has_headers(false)
            .from_path(&self.csv_file);
        match reader {
            Ok(mut reader) => {
                let mut temp_game_data = GameData::new("ai".to_string(),"ai_2".to_string());
                for result in reader.records(){
                    match result {
                        Ok(record) =>{
                            let mut index = 0;
                            for item in record.iter(){
                                match item{
                                    "-1"|"0"|"1" => {
                                        temp_game_data.periodic_state_of_cells[index] = item.parse::<i8>().unwrap();
                                        index += 1;
                                    }
                                    "" => {
                                        if index >= 8 {
                                            temp_game_data.state_of_cells_list.push(temp_game_data.periodic_state_of_cells.clone());
                                        }
                                        index = 0;
                                    }
                                    "ai"|"ai_2"|"draw" => {
                                        temp_game_data.winner.push_str(item);
                                        temp_game_data.state_of_cells_list.push(temp_game_data.periodic_state_of_cells);
                                        index = 0;
                                        self.game_data.push(temp_game_data.clone());
                                        //if true the game ends
                                        temp_game_data = GameData::new("ai".to_string(),"ai_2".to_string());
                                    }
                                    _ => {
                                        println!("item: {}", item);
                                    }
                                }
                            }
                        }
                        Err(error) => {
                            println!("Error reading record: {}", error);
                        }
                    }
                }
            }
            Err(error) => {
                println!("Error reading file: {}", error);
            }
        }
    }
}