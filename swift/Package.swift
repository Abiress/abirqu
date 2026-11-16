// swift-tools-version:5.9
import PackageDescription
import Foundation

let libPath = ProcessInfo.processInfo.environment["ABIRQU_LIB_DIR"] ?? "../target/release"

let package = Package(
    name: "AbirQu",
    products: [
        .library(name: "AbirQu", targets: ["AbirQu"]),
    ],
    targets: [
        .target(
            name: "AbirQu",
            path: "Sources/AbirQu",
            linkerSettings: [
                .linkedLibrary("abirqu_core"),
                .unsafeFlags(["-L\(libPath)"]),
            ]
        ),
        .testTarget(
            name: "AbirQuTests",
            dependencies: ["AbirQu"],
            path: "Tests/AbirQuTests",
            linkerSettings: [
                .linkedLibrary("abirqu_core"),
                .unsafeFlags(["-L\(libPath)"]),
            ]
        ),
    ]
)
