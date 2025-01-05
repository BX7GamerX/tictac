pub struct GameData {
    pub winner: String,
    pub player1: String,
    pub player2: String,
    pub state_of_cells_list: Vec<[i8;9]>,
    pub periodic_State_of_cells : [i8;9],
}
impl GameData {
    pub fn new(player1: String, player2: String) -> GameData {
        GameData {
            winner : String::from(""),
            player1,
            player2,
            state_of_cells_list : Vec::new(),
            periodic_State_of_cells : [0,0,0,0,0,0,0,0,0],
        }
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
    pub fn read_datat(&self) {
        println!("Reading data from file: {}", self.csv_file);
    }
}