plugins {
    kotlin("jvm") version "1.9.23"
}

group = "com.abirqu"
version = "1.1.1"

repositories {
    mavenCentral()
}

dependencies {
    implementation("net.java.dev.jna:jna:5.14.0")
    testImplementation("org.junit.jupiter:junit-jupiter:5.10.2")
    testRuntimeOnly("org.junit.platform:junit-platform-launcher")
}

kotlin {
    jvmToolchain(11)
}

tasks.test {
    useJUnitPlatform()
    systemProperty("jna.library.path", System.getenv("LD_LIBRARY_PATH") ?: ".")
}
