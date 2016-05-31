use std::process::{Command, Output};
use std::path::Path;
use std::fs::File;
use std::error::Error;
use std::collections::BTreeMap;

extern crate serde_pickle;
use serde_pickle::de::from_reader;
use serde_pickle::value::{HashableValue, Value};

fn main() {
    println!("Downloading and building CLDR data...");
    let output: Output = Command::new("python3").args(&["scripts/download_import_cldr.py"])
            .output()
            .unwrap_or_else(|e| {
                panic!("failed to execute process: {}", e)
            });
    println!("errors: {}", String::from_utf8_lossy(&output.stderr));
    println!("\n\nTesting...");

    let path = Path::new("cldr/locale-data/root.dat");
    let file =  match File::open(&path) {
        Err(why) => panic!("couldn't open {}: {}", path.display(),
                                                   why.description()),
        Ok(file) => file,
    };

    let v: BTreeMap<HashableValue, Value> = from_reader(file).unwrap();

    // if this doesn't work, something bad happened
    println!("Dumping a deserialized data structure:\n\n{:?}", v);
}
