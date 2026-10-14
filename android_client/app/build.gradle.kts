plugins { id("com.android.application"); id("org.jetbrains.kotlin.android") }
android {
    namespace = "ph.korena.pharmaledger"
    compileSdk = 35
    defaultConfig { applicationId = "ph.korena.pharmaledger"; minSdk = 26; targetSdk = 35; versionCode = 1; versionName = "1.0" }
    buildTypes { release { isMinifyEnabled = false } }
    compileOptions { sourceCompatibility = JavaVersion.VERSION_17; targetCompatibility = JavaVersion.VERSION_17 }
    kotlinOptions { jvmTarget = "17" }
}
