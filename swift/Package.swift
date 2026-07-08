// swift-tools-version:5.9
import PackageDescription

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
                .unsafeFlags(["-L/home/abir/ai_dev/abirqu/target/release"]),
            ]
        ),
        .testTarget(
            name: "AbirQuTests",
            dependencies: ["AbirQu"],
            path: "Tests/AbirQuTests",
            linkerSettings: [
                .linkedLibrary("abirqu_core"),
                .unsafeFlags(["-L/home/abir/ai_dev/abirqu/target/release"]),
            ]
        ),
    ]
)
