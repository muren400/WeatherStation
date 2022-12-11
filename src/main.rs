use std::fs;
use std::fs::OpenOptions;
use std::io;
use std::path::PathBuf;
use std::io::Write;
use std::time::{SystemTime, UNIX_EPOCH};
use std::net::SocketAddr;
use std::error::Error;
use std::env;

use std::collections::HashMap;

use url::form_urlencoded;

use chrono::{Datelike, Timelike, Utc};

use futures::stream::TryStreamExt;

use hyper::service::{make_service_fn, service_fn};
use hyper::{Body, Method, Request, Response, Server, StatusCode};

fn getFullPath(filePath: &str) -> io::Result<PathBuf> {
    let mut path = env::current_exe()?;
    path.pop();
    path.push(filePath);
    Ok(path)
}

fn getTodaysDataPath() -> String {
    let now = Utc::now();
    return format!("data/data_{}-{:02}-{:02}.csv", now.year(),  now.month(), now.day());
}

fn getFileContent(filePath: &str) -> String {
    let path = getFullPath(filePath).expect("");

    println!("get file {:?}", path.display());
    return fs::read_to_string(path).expect("404");
}

fn storeTemperature(temp: f32) {
    let now = Utc::now();
    let timestamp = now.timestamp_millis()/1000;

    let line = format!("{}, {}\n", timestamp, temp);
    let filePath = getFullPath(&getTodaysDataPath()).expect("");

    println!("write to file {} {}", filePath.display(), line);

    let mut file = OpenOptions::new().create(true).append(true).open(filePath).unwrap();
    if let Err(e) = writeln!(file, "{}", line) {
        eprintln!("Couldn't write to file: {}", e);
    }
}

/// This is our service handler. It receives a Request, routes on its
/// path, and returns a Future of a Response.
async fn echo(req: Request<Body>) -> Result<Response<Body>, hyper::Error> {
    match (req.method(), req.uri().path()) {
        (&Method::GET, "/") => {
            let indexHtml = getFileContent("gui/index.html");
            Ok(Response::new(Body::from(indexHtml)))
        }

        (&Method::GET, "/query") => {
            let data = getFileContent(&getTodaysDataPath());
            Ok(Response::new(Body::from(data)))
        }

        (&Method::GET, "/putTemperature") => {
            let query = if let Some(q) = req.uri().query() {
                q
            } else {
                return Ok(Response::builder()
                    .status(StatusCode::UNPROCESSABLE_ENTITY)
                    .body("error".into())
                    .unwrap());
            };
            let params = form_urlencoded::parse(query.as_bytes())
                .into_owned()
                .collect::<HashMap<String, String>>();
            let temperature = if let Some(p) = params.get("temp") {
                p
            } else {
                return Ok(Response::builder()
                    .status(StatusCode::UNPROCESSABLE_ENTITY)
                    .body("error".into())
                    .unwrap());
            };

            storeTemperature(temperature.parse().unwrap());

            let body = format!("write temperature {}", temperature);
            Ok(Response::new(body.into()))
            // storeTemperature();
            // Ok(Response::new(Body::from("ok")))
        }

        // Return the 404 Not Found for other routes.
        _ => {
            let mut not_found = Response::default();
            *not_found.status_mut() = StatusCode::NOT_FOUND;
            Ok(not_found)
        }
    }
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
    let addr = ([127, 0, 0, 1], 13337).into();

    let service = make_service_fn(|_| async { Ok::<_, hyper::Error>(service_fn(echo)) });

    let server = Server::bind(&addr).serve(service);

    println!("Listening on http://{}", addr);

    server.await?;

    Ok(())
}
