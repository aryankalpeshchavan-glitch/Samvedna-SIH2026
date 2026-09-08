# ProGuard rules for CrisisCore

# Retrofit
-keepattributes Signature
-keepattributes Exceptions
-keepattributes *Annotation*

-keep class retrofit2.** { *; }
-keepclasseswithmembers class * {
    @retrofit2.http.* <methods>;
}

# Kotlinx Serialization
-keepattributes *Annotation*, InnerClasses
-dontnote kotlinx.serialization.AnnotationsKt

-keepclassmembers @kotlinx.serialization.Serializable class ** {
    *** Companion;
}
-keepclasseswithmembers class **$$serializer {
    *** INSTANCE;
}

# Keep data models for serialization
-keep class com.crisiscore.app.data.model.** { *; }

# OkHttp
-dontwarn okhttp3.**
-dontwarn okio.**
-dontwarn javax.annotation.**

# MapLibre
-keep class com.mapbox.** { *; }
-keep class org.maplibre.** { *; }
-dontwarn org.maplibre.**

# Room
-keep class androidx.room.** { *; }
-dontwarn androidx.room.**
