use mavlink::{ardupilotmega::MavMessage, MavlinkVersion};
use std::sync::Arc;

pub type MavConn = Arc<Box<dyn mavlink::MavConnection<MavMessage> + Sync + Send>>;

pub fn connect_to_vehicle(connection_string: &str) -> Result<MavConn, ()> {
    println!("Connecting to: {connection_string}");

    let mut conn = mavlink::connect::<MavMessage>(connection_string).map_err(|e| {
        eprintln!("✗ Failed to establish connection: {e}");
    })?;

    conn.set_protocol_version(MavlinkVersion::V2);
    println!("✓ Connection established\n");

    Ok(Arc::new(conn))
}
