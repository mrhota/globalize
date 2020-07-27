use std::process::{Command, Output};
use std::path::Path;
use std::fs::File;
use std::error::Error;
use std::collections::BTreeMap;

extern crate rmp as msgpack;

fn main() {
    println!("Downloading and building CLDR data...");
    let output: Output = Command::new("python3").args(&["scripts/download_import_cldr.py"])
            .output()
            .unwrap_or_else(|e| {
                panic!("failed to execute process: {}", e)
            });
    println!("errors: {}", String::from_utf8_lossy(&output.stderr));

    let path = Path::new("cldr/locale-data/root.json");
    let file =  match File::open(&path) {
        Err(why) => panic!("couldn't open {}: {}", path.display(),
                                                   why.description()),
        Ok(file) => file,
    };
}
