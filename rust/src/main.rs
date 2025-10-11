mod connection;
mod display;
mod messages;
mod receiver;
mod utils;

use clap::Parser;
use std::process;

#[derive(Parser)]
struct Args {
    /// Connection string (e.g., udpin:0.0.0.0:14550)
    connection: String,

    /// Filter messages to display (comma-separated, e.g., HEARTBEAT,ATTITUDE,GPS_RAW_INT)
    #[arg(long, value_delimiter = ',')]
    messages: Option<Vec<String>>,
}

fn main() {
    let args = Args::parse();

    let filter = utils::build_message_filter(args.messages);
    let vehicle = connect_or_exit(&args.connection);

    messages::initialize(&vehicle);
    messages::start_heartbeat(&vehicle);
    receiver::run(&vehicle, filter);
}

fn connect_or_exit(connection_string: &str) -> connection::MavConn {
    connection::connect_to_vehicle(connection_string).unwrap_or_else(|_| {
        eprintln!("✗ Failed to connect, exiting");
        process::exit(1)
    })
}
