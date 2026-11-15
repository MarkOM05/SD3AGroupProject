package com.example.bank

import android.app.Activity
import android.content.Context
import android.os.Bundle
import android.widget.Toast
import androidx.activity.ComponentActivity
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.activity.result.ActivityResultLauncher
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.navigation.NavController
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import com.example.bank.ui.theme.BankTheme
import com.google.firebase.auth.FirebaseAuth
import com.google.firebase.firestore.ktx.firestore
import com.google.firebase.firestore.FirebaseFirestore
import com.stripe.android.PaymentConfiguration
import com.stripe.android.paymentsheet.PaymentSheet
import com.stripe.android.paymentsheet.PaymentSheetResult
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import retrofit2.http.Body
import retrofit2.http.GET
import retrofit2.http.POST
import retrofit2.http.Path
import retrofit2.http.Query
import java.util.concurrent.TimeUnit

// =============================================================================
//  Session state
// =============================================================================
object SessionState {
    var currentApplicationId by mutableStateOf<String?>(null)
    var currentUserId by mutableStateOf<String?>(null)
}

// =============================================================================
//  API models — names match the live OpenAPI spec exactly
// =============================================================================
data class PropertyPayload(
    val county: String,
    val sizeSqm: Int,
    val bedrooms: Int,
    val type: String,
    val berRating: String,
    val askingPrice: Int
)

data class ApplicationForm(
    val loanType: String,
    val income: Int,
    val debts: Int,
    val deposit: Int,
    val termYears: Int,
    val property: PropertyPayload
)

data class PropertySpec(
    val county: String,
    val sizeSqm: Int,
    val bedrooms: Int,
    val type: String,
    val berRating: String
)

data class AffordabilityIn(
    val income: Int,
    val debts: Int,
    val deposit: Int,
    val propertyValue: Int,
    val termYears: Int
)

data class StressTestCreate(
    val rateShockBps: Int
)

// =============================================================================
//  Bank API — matches https://sd3agroupproject.onrender.com/docs
// =============================================================================
interface BankApi {
    @GET("/health")
    suspend fun health(): String

    @POST("/applications")
    suspend fun createApplication(@Body form: ApplicationForm): String

    @POST("/valuation")
    suspend fun valuation(@Body spec: PropertySpec): String

    @POST("/affordability")
    suspend fun affordability(@Body input: AffordabilityIn): String

    @POST("/applications/{app_id}/deliberate")
    suspend fun deliberate(@Path("app_id") appId: String): String

    @POST("/applications/{app_id}/approve")
    suspend fun approve(@Path("app_id") appId: String): String

    @POST("/applications/{app_id}/decline")
    suspend fun decline(@Path("app_id") appId: String): String

    @GET("/applications/{app_id}/audit-pack")
    suspend fun auditPack(
        @Path("app_id") appId: String,
        @Query("format") format: String = "pdf"
    ): okhttp3.ResponseBody

    @POST("/stress-test")
    suspend fun stressTest(@Body body: StressTestCreate): String

    @POST("/payments/create-intent")
    suspend fun createPaymentIntent(): String
}

// =============================================================================
//  Retrofit client with Firebase auth + long timeout (Render cold starts)
// =============================================================================
object RetrofitClient {
    private const val BASE_URL = "https://sd3agroupproject.onrender.com/"

    private val authInterceptor = okhttp3.Interceptor { chain ->
        val token = try {
            FirebaseAuth.getInstance().currentUser
                ?.getIdToken(false)
                ?.result
                ?.token
        } catch (_: Throwable) { null }

        val req = chain.request().newBuilder().apply {
            if (token != null) header("authorization", "Bearer $token")
            header("Accept", "application/json")
        }.build()
        chain.proceed(req)
    }

    private val client: OkHttpClient by lazy {
        val logging = HttpLoggingInterceptor().apply {
            level = HttpLoggingInterceptor.Level.BODY
        }
        OkHttpClient.Builder()
            .addInterceptor(authInterceptor)
            .addInterceptor(logging)
            .connectTimeout(60, TimeUnit.SECONDS)
            .readTimeout(60, TimeUnit.SECONDS)
            .writeTimeout(60, TimeUnit.SECONDS)
            .build()
    }

    val api: BankApi by lazy {
        Retrofit.Builder()
            .baseUrl(BASE_URL)
            .client(client)
            .addConverterFactory(GsonConverterFactory.create())
            .build()
            .create(BankApi::class.java)
    }
}

// =============================================================================
//  Local-only model for the Loan Status screen
// =============================================================================
data class LoanStatusView(
    val applicationId: String,
    val ltv: Double,
    val dti: Double,
    val approvalLikelihood: String,
    val status: String,
    val declineReason: String? = null,
    val transactionRef: String? = null
)

// =============================================================================
//  Activity
// =============================================================================
class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContent {
            BankTheme(darkTheme = isDarkMode) {
                MainApp()
            }
        }
    }
}

var isDarkMode by mutableStateOf(false)

// =============================================================================
//  Root navigation
// =============================================================================
@Composable
fun MainApp() {
    val navController = rememberNavController()

    val backgroundColor = if (isDarkMode) Color(0xFF121212) else Color(0xFFF7F8FA)
    val textColor = if (isDarkMode) Color.White else Color.Black
    val primaryColor = if (isDarkMode) Color(0xFFFFD100) else Color(0xFF003366)
    val cardColor = if (isDarkMode) Color(0xFF1E1E1E) else Color(0xFFFFFFFF)

    MaterialTheme(
        colorScheme = if (isDarkMode) darkColorScheme() else lightColorScheme()
    ) {
        Scaffold(
            modifier = Modifier.fillMaxSize(),
            containerColor = backgroundColor
        ) { innerPadding ->
            NavHost(
                navController = navController,
                startDestination = "login",
                modifier = Modifier.padding(innerPadding)
            ) {
                composable("login") {
                    LoginScreen(navController, textColor, primaryColor)
                }
                composable("dashboard") {
                    DashboardScreen(navController, textColor, primaryColor, cardColor)
                }
                composable("affordability") {
                    Affordability(navController, "Affordability & Loan Application", textColor, primaryColor, cardColor)
                }
                composable("property_checker") {
                    FairPriceCheckerScreen(navController, textColor, primaryColor, cardColor)
                }
                composable("status") {
                    LoanStatusScreen(navController, textColor, primaryColor, cardColor)
                }
                composable("contact") {
                    PlaceholderScreen(navController, "Broker / Official Contact", textColor, primaryColor)
                }
                composable("payments") {
                    PaymentsScreen(navController, textColor, primaryColor, cardColor)
                }
                composable("support") {
                    PlaceholderScreen(navController, "Support & Reviews", textColor, primaryColor)
                }
            }
        }
    }
}

// =============================================================================
//  Dashboard
// =============================================================================
data class DashboardItem(
    val id: Int,
    val label: String,
    val route: String,
    val icon: ImageVector
)

@Composable
fun DashboardScreen(
    navController: NavController,
    textColor: Color,
    primaryColor: Color,
    cardColor: Color
) {
    val items = listOf(
        DashboardItem(1, "Affordability & Loan", "affordability", Icons.Default.Calculate),
        DashboardItem(2, "Property Checker", "property_checker", Icons.Default.Home),
        DashboardItem(3, "AL-AI Status", "status", Icons.Default.Info),
        DashboardItem(4, "Broker Contact", "contact", Icons.Default.Person),
        DashboardItem(5, "Payments", "payments", Icons.Default.Payment),
        DashboardItem(6, "Support & Reviews", "support", Icons.Default.SupportAgent),
    )

    Column(modifier = Modifier.fillMaxSize().padding(16.dp)) {
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Text("Dashboard", fontSize = 24.sp, fontWeight = FontWeight.Bold, color = textColor)
            IconButton(onClick = { isDarkMode = !isDarkMode }) {
                Icon(
                    imageVector = if (isDarkMode) Icons.Default.LightMode else Icons.Default.DarkMode,
                    contentDescription = "Toggle Theme",
                    tint = primaryColor
                )
            }
        }
        Spacer(Modifier.height(16.dp))
        LazyColumn(
            modifier = Modifier.fillMaxSize(),
            verticalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            items(items, key = { it.id }) { item ->
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .clip(RoundedCornerShape(8.dp))
                        .clickable { navController.navigate(item.route) }
                        .padding(16.dp),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Icon(item.icon, contentDescription = null, tint = textColor, modifier = Modifier.size(24.dp))
                    Spacer(Modifier.width(16.dp))
                    Text(item.label, fontSize = 16.sp, color = textColor)
                }
            }
        }
    }
}

// =============================================================================
//  Login
// =============================================================================
@Composable
fun LoginScreen(
    navController: NavController,
    textColor: Color,
    primaryColor: Color
) {
    var email by remember { mutableStateOf("") }
    var password by remember { mutableStateOf("") }
    val context = LocalContext.current
    val scope = rememberCoroutineScope()
    var isLoading by remember { mutableStateOf(false) }

    Column(
        modifier = Modifier.fillMaxSize().padding(24.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center
    ) {
        Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.End) {
            IconButton(onClick = { isDarkMode = !isDarkMode }) {
                Icon(
                    imageVector = if (isDarkMode) Icons.Default.LightMode else Icons.Default.DarkMode,
                    contentDescription = "Toggle Theme",
                    tint = primaryColor
                )
            }
        }

        Icon(
            imageVector = Icons.Default.AccountBalance,
            contentDescription = "Bank Logo",
            tint = primaryColor,
            modifier = Modifier.size(64.dp)
        )
        Spacer(Modifier.height(16.dp))
        Text("AL Agentic Lender", fontSize = 28.sp, fontWeight = FontWeight.Bold, color = textColor)
        Spacer(Modifier.height(32.dp))

        OutlinedTextField(
            value = email,
            onValueChange = { email = it },
            label = { Text("Email") },
            modifier = Modifier.fillMaxWidth()
        )
        Spacer(Modifier.height(16.dp))
        OutlinedTextField(
            value = password,
            onValueChange = { password = it },
            label = { Text("Password") },
            visualTransformation = PasswordVisualTransformation(),
            modifier = Modifier.fillMaxWidth()
        )
        Spacer(Modifier.height(24.dp))

        Button(
            onClick = {
                if (email.isBlank() || password.isBlank()) {
                    Toast.makeText(context, "Please enter details", Toast.LENGTH_SHORT).show()
                    return@Button
                }
                isLoading = true
                val auth = FirebaseAuth.getInstance()
                auth.signInWithEmailAndPassword(email.trim(), password)
                    .addOnSuccessListener { result ->
                        isLoading = false
                        SessionState.currentUserId = result.user?.uid
                        Toast.makeText(context, "Login successful", Toast.LENGTH_SHORT).show()
                        navController.navigate("dashboard") {
                            popUpTo("login") { inclusive = true }
                        }
                    }
                    .addOnFailureListener { e ->
                        isLoading = false
                        Toast.makeText(context, "Login failed: ${e.message}", Toast.LENGTH_LONG).show()
                    }
            },
            colors = ButtonDefaults.buttonColors(containerColor = primaryColor),
            modifier = Modifier.fillMaxWidth().height(50.dp),
            enabled = !isLoading
        ) {
            if (isLoading) CircularProgressIndicator(
                modifier = Modifier.size(20.dp), color = Color.White, strokeWidth = 2.dp
            ) else Text("Login")
        }
    }
}

// =============================================================================
//  Affordability — calls /affordability (string response, displayed as-is)
// =============================================================================
@Composable
fun Affordability(
    navController: NavController,
    title: String,
    textColor: Color,
    primaryColor: Color,
    cardColor: Color
) {
    var income by remember { mutableStateOf("") }
    var debt by remember { mutableStateOf("") }
    var deposit by remember { mutableStateOf("") }
    var propertyValue by remember { mutableStateOf("") }
    var term by remember { mutableStateOf("30") }

    var isLoading by remember { mutableStateOf(false) }
    var responseText by remember { mutableStateOf<String?>(null) }
    var errorMsg by remember { mutableStateOf<String?>(null) }

    val context = LocalContext.current
    val scope = rememberCoroutineScope()

    val incomeInt = income.toIntOrNull()
    val debtInt = debt.toIntOrNull() ?: 0
    val depositInt = deposit.toIntOrNull()
    val propertyValueInt = propertyValue.toIntOrNull()
    val termInt = term.toIntOrNull() ?: 30

    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(16.dp)
            .verticalScroll(rememberScrollState())
    ) {
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Text(title, fontSize = 20.sp, fontWeight = FontWeight.Bold, color = textColor)
            IconButton(onClick = { isDarkMode = !isDarkMode }) {
                Icon(
                    imageVector = if (isDarkMode) Icons.Default.LightMode else Icons.Default.DarkMode,
                    contentDescription = "Toggle Theme",
                    tint = primaryColor
                )
            }
        }
        Spacer(Modifier.height(16.dp))

        OutlinedTextField(
            value = income, onValueChange = { income = it },
            label = { Text("Annual Income (€)") },
            keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
            modifier = Modifier.fillMaxWidth()
        )
        Spacer(Modifier.height(8.dp))
        OutlinedTextField(
            value = debt, onValueChange = { debt = it },
            label = { Text("Existing Debts (€)") },
            keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
            modifier = Modifier.fillMaxWidth()
        )
        Spacer(Modifier.height(8.dp))
        OutlinedTextField(
            value = deposit, onValueChange = { deposit = it },
            label = { Text("Deposit (€)") },
            keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
            modifier = Modifier.fillMaxWidth()
        )
        Spacer(Modifier.height(8.dp))
        OutlinedTextField(
            value = propertyValue, onValueChange = { propertyValue = it },
            label = { Text("Property Value (€)") },
            keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
            modifier = Modifier.fillMaxWidth()
        )
        Spacer(Modifier.height(8.dp))
        OutlinedTextField(
            value = term, onValueChange = { term = it },
            label = { Text("Mortgage Term (Years, 5–35)") },
            keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
            modifier = Modifier.fillMaxWidth()
        )

        Spacer(Modifier.height(24.dp))

        errorMsg?.let {
            Text(it, color = Color.Red, fontSize = 14.sp)
            Spacer(Modifier.height(8.dp))
        }

        if (isLoading) {
            Box(Modifier.fillMaxWidth(), contentAlignment = Alignment.Center) {
                CircularProgressIndicator(color = primaryColor)
            }
            Spacer(Modifier.height(16.dp))
        }

        responseText?.let { raw ->
            Card(
                modifier = Modifier.fillMaxWidth(),
                colors = CardDefaults.cardColors(containerColor = cardColor),
                elevation = CardDefaults.cardElevation(4.dp)
            ) {
                Column(Modifier.padding(16.dp)) {
                    Text("Affordability Result", fontWeight = FontWeight.Bold, color = textColor)
                    Spacer(Modifier.height(8.dp))
                    Text(raw, color = primaryColor)
                }
            }
            Spacer(Modifier.height(16.dp))
        }

        Button(
            onClick = {
                if (incomeInt == null || incomeInt <= 0 ||
                    depositInt == null || depositInt < 0 ||
                    propertyValueInt == null || propertyValueInt <= 0
                ) {
                    errorMsg = "Please fill income, deposit and property value with positive numbers"
                    return@Button
                }
                if (termInt !in 5..35) {
                    errorMsg = "Term must be between 5 and 35 years"
                    return@Button
                }
                errorMsg = null
                scope.launch {
                    isLoading = true
                    try {
                        val input = AffordabilityIn(
                            income = incomeInt,
                            debts = debtInt,
                            deposit = depositInt,
                            propertyValue = propertyValueInt,
                            termYears = termInt
                        )
                        responseText = RetrofitClient.api.affordability(input)
                    } catch (e: Exception) {
                        errorMsg = "API error: ${e.message}"
                    } finally {
                        isLoading = false
                    }
                }
            },
            modifier = Modifier.fillMaxWidth(),
            colors = ButtonDefaults.buttonColors(containerColor = primaryColor),
            enabled = !isLoading
        ) {
            Text("Check Affordability")
        }

        Spacer(Modifier.height(8.dp))
        OutlinedButton(
            onClick = {
                // Submit a full application using the same figures
                if (incomeInt == null || incomeInt <= 0 ||
                    depositInt == null || depositInt < 0 ||
                    propertyValueInt == null || propertyValueInt <= 0
                ) {
                    errorMsg = "Fill the form before submitting the application"
                    return@OutlinedButton
                }
                scope.launch {
                    isLoading = true
                    try {
                        val form = ApplicationForm(
                            loanType = "Mortgage",
                            income = incomeInt,
                            debts = debtInt,
                            deposit = depositInt,
                            termYears = termInt.coerceIn(1, 40),
                            property = PropertyPayload(
                                county = "Dublin",
                                sizeSqm = 95,
                                bedrooms = 3,
                                type = "Semi-D",
                                berRating = "B2",
                                askingPrice = propertyValueInt
                            )
                        )
                        val appIdRaw = RetrofitClient.api.createApplication(form)
                        val appId = appIdRaw.trim('"', ' ', '\n')
                        SessionState.currentApplicationId = appId
                        Toast.makeText(context, "Application submitted: $appId", Toast.LENGTH_LONG).show()
                    } catch (e: Exception) {
                        errorMsg = "Submit failed: ${e.message}"
                    } finally {
                        isLoading = false
                    }
                }
            },
            modifier = Modifier.fillMaxWidth()
        ) {
            Text("Submit Full Application", color = textColor)
        }

        Spacer(Modifier.height(8.dp))
        OutlinedButton(
            onClick = { navController.navigate("dashboard") },
            modifier = Modifier.fillMaxWidth()
        ) {
            Text("Back to Dashboard", color = textColor)
        }
    }
}

// =============================================================================
//  Fair Price Checker — calls /valuation, builds comparison client-side
// =============================================================================
private val BER_VALUES = listOf("A1", "A2", "A3", "B1", "B2", "B3", "C1", "C2", "C3", "D1", "D2", "E1", "E2", "F", "G")
private val PROPERTY_TYPES = listOf("Semi-D", "Detached", "Terraced", "Apartment", "Bungalow", "Duplex")
private val COUNTIES = listOf("Dublin", "Cork", "Galway", "Limerick", "Waterford", "Kildare", "Meath", "Wicklow")

@Composable
fun FairPriceCheckerScreen(
    navController: NavController,
    textColor: Color,
    primaryColor: Color,
    cardColor: Color
) {
    var county by remember { mutableStateOf("Dublin") }
    var sizeSqm by remember { mutableStateOf("") }
    var bedrooms by remember { mutableStateOf("") }
    var propertyType by remember { mutableStateOf("Semi-D") }
    var ber by remember { mutableStateOf("B2") }
    var askingPrice by remember { mutableStateOf("") }

    var isLoading by remember { mutableStateOf(false) }
    var estimate by remember { mutableStateOf<Double?>(null) }
    var errorMsg by remember { mutableStateOf<String?>(null) }

    val context = LocalContext.current
    val scope = rememberCoroutineScope()

    Column(
        modifier = Modifier.fillMaxSize().padding(16.dp).verticalScroll(rememberScrollState())
    ) {
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Text("Fair Price Checker", fontSize = 20.sp, fontWeight = FontWeight.Bold, color = textColor)
            IconButton(onClick = { isDarkMode = !isDarkMode }) {
                Icon(
                    imageVector = if (isDarkMode) Icons.Default.LightMode else Icons.Default.DarkMode,
                    contentDescription = "Toggle Theme",
                    tint = primaryColor
                )
            }
        }
        Spacer(Modifier.height(16.dp))

        OutlinedTextField(
            value = county, onValueChange = { county = it },
            label = { Text("County (e.g. Dublin)") },
            modifier = Modifier.fillMaxWidth()
        )
        Spacer(Modifier.height(8.dp))
        OutlinedTextField(
            value = sizeSqm, onValueChange = { sizeSqm = it },
            label = { Text("Floor area (m²)") },
            keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
            modifier = Modifier.fillMaxWidth()
        )
        Spacer(Modifier.height(8.dp))
        OutlinedTextField(
            value = sizeSqm, onValueChange = { sizeSqm = it },
            label = { Text("Floor area (m²)") },
            keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
            modifier = Modifier.fillMaxWidth()
        )
        Spacer(Modifier.height(8.dp))
        OutlinedTextField(
            value = bedrooms, onValueChange = { bedrooms = it },
            label = { Text("Bedrooms") },
            keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
            modifier = Modifier.fillMaxWidth()
        )
        Spacer(Modifier.height(8.dp))
        OutlinedTextField(
            value = propertyType, onValueChange = { propertyType = it },
            label = { Text("Property type (${PROPERTY_TYPES.joinToString("/")})") },
            modifier = Modifier.fillMaxWidth()
        )
        Spacer(Modifier.height(8.dp))
        OutlinedTextField(
            value = ber, onValueChange = { ber = it },
            label = { Text("BER rating (A1..G)") },
            modifier = Modifier.fillMaxWidth()
        )
        Spacer(Modifier.height(8.dp))
        OutlinedTextField(
            value = askingPrice, onValueChange = { askingPrice = it },
            label = { Text("Asking price (€)") },
            keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
            modifier = Modifier.fillMaxWidth()
        )

        Spacer(Modifier.height(16.dp))
        errorMsg?.let {
            Text(it, color = Color.Red, fontSize = 14.sp)
            Spacer(Modifier.height(8.dp))
        }

        Button(
            onClick = {
                // On-device validation
                val sizeVal = sizeSqm.toIntOrNull()
                val bedVal = bedrooms.toIntOrNull()
                val askVal = askingPrice.toIntOrNull()
                when {
                    sizeVal == null || sizeVal <= 0 -> { errorMsg = "Floor area must be a positive number"; return@Button }
                    bedVal == null || bedVal < 0 -> { errorMsg = "Bedrooms must be 0 or more"; return@Button }
                    askVal == null || askVal <= 0 -> { errorMsg = "Asking price must be a positive number"; return@Button }
                    county.isBlank() -> { errorMsg = "County is required"; return@Button }
                    propertyType.isBlank() -> { errorMsg = "Property type is required"; return@Button }
                    ber !in BER_VALUES -> { errorMsg = "BER must be one of ${BER_VALUES.joinToString(", ")}"; return@Button }
                }
                errorMsg = null
                scope.launch {
                    isLoading = true
                    estimate = null
                    try {
                        val spec = PropertySpec(
                            county = county,
                            sizeSqm = sizeVal!!,
                            bedrooms = bedVal!!,
                            type = propertyType,
                            berRating = ber
                        )
                        val raw = RetrofitClient.api.valuation(spec)
                        // Response is a bare JSON string; strip any quotes/currency
                        val cleaned = raw.replace(Regex("[^0-9.]"), "")
                        val parsed = cleaned.toDoubleOrNull()
                        if (parsed == null) {
                            errorMsg = "Could not parse valuation response: $raw"
                        } else {
                            estimate = parsed
                        }
                    } catch (e: Exception) {
                        errorMsg = "Valuation failed: ${e.message}"
                    } finally {
                        isLoading = false
                    }
                }
            },
            enabled = !isLoading,
            modifier = Modifier.fillMaxWidth().height(50.dp),
            colors = ButtonDefaults.buttonColors(containerColor = primaryColor)
        ) {
            if (isLoading) CircularProgressIndicator(
                modifier = Modifier.size(20.dp), color = Color.White, strokeWidth = 2.dp
            ) else Text("Check Price")
        }

        Spacer(Modifier.height(24.dp))

        estimate?.let { est ->
            val asking = askingPrice.toDoubleOrNull() ?: 0.0
            val diffPct = if (est > 0) ((asking - est) / est) * 100.0 else 0.0
            Card(
                modifier = Modifier.fillMaxWidth(),
                colors = CardDefaults.cardColors(containerColor = cardColor),
                elevation = CardDefaults.cardElevation(4.dp)
            ) {
                Column(Modifier.padding(16.dp)) {
                    Text("Estimated Value", color = textColor)
                    Text(
                        "€%,.0f".format(est),
                        fontSize = 32.sp, fontWeight = FontWeight.Bold, color = primaryColor
                    )
                    Spacer(Modifier.height(8.dp))
                    HorizontalDivider()
                    Spacer(Modifier.height(8.dp))
                    Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                        Text("Asking price", color = textColor)
                        Text("€%,.0f".format(asking), color = textColor)
                    }
                    Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                        Text("Difference", color = textColor)
                        val sign = if (diffPct >= 0) "+" else ""
                        Text(
                            "$sign%.1f%% vs estimate".format(diffPct),
                            color = if (diffPct > 10) Color.Red else primaryColor,
                            fontWeight = FontWeight.Bold
                        )
                    }
                }
            }
        }

        Spacer(Modifier.height(16.dp))
        OutlinedButton(
            onClick = { navController.navigate("dashboard") },
            modifier = Modifier.fillMaxWidth()
        ) { Text("Back to Dashboard", color = textColor) }
    }
}

// =============================================================================
//  Payments — Stripe PaymentSheet
// =============================================================================
@Composable
fun PaymentsScreen(
    navController: NavController,
    textColor: Color,
    primaryColor: Color,
    cardColor: Color
) {
    val context = LocalContext.current
    val scope = rememberCoroutineScope()

    val applicationId = SessionState.currentApplicationId ?: "—"
    var amountCents by remember { mutableStateOf(15000) } // €150 default; overwritten by server when available
    var status by remember { mutableStateOf("Not paid") }
    var isPaying by remember { mutableStateOf(false) }

    Column(
        modifier = Modifier.fillMaxSize().padding(16.dp).verticalScroll(rememberScrollState())
    ) {
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Text(
                "Application Fee",
                fontSize = 22.sp,
                fontWeight = FontWeight.Bold,
                color = textColor
            )
            IconButton(onClick = { isDarkMode = !isDarkMode }) {
                Icon(
                    imageVector = if (isDarkMode) Icons.Default.LightMode else Icons.Default.DarkMode,
                    contentDescription = "Toggle Theme",
                    tint = primaryColor
                )
            }
        }
        Spacer(Modifier.height(24.dp))

        Card(
            modifier = Modifier.fillMaxWidth(),
            colors = CardDefaults.cardColors(containerColor = cardColor)
        ) {
            Column(Modifier.padding(16.dp)) {
                Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                    Text("Application", color = textColor)
                    Text("#$applicationId", color = textColor)
                }
                Spacer(Modifier.height(8.dp))
                Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                    Text("Appraisal fee", color = textColor)
                    Text("€%.2f".format(amountCents / 100.0), color = textColor)
                }
                Spacer(Modifier.height(8.dp))
                HorizontalDivider()
                Spacer(Modifier.height(8.dp))
                Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                    Text("Status", fontWeight = FontWeight.Bold, color = textColor)
                    Text(
                        status,
                        fontWeight = FontWeight.Bold,
                        color = if (status == "Paid") primaryColor else Color(0xFFB8860B)
                    )
                }
            }
        }

        Spacer(Modifier.height(24.dp))

        if (status != "Paid") {
            Button(
                onClick = {
                    if (isPaying) return@Button
                    isPaying = true
                    scope.launch {
                        try {
                            // Step 1: Server creates PaymentIntent and returns a client secret
                            val raw = RetrofitClient.api.createPaymentIntent()
                            val clientSecret = raw.trim('"', ' ', '\n')

                            // Step 2: Initialize Stripe with Publishable Key
                            PaymentConfiguration.init(
                                context, "pk_test_51UUIWRCPs2UWh2CjJRtml8dddBIskb7XEL9WpJuxN1AqwqNDwRXVMFPrKrOLNgHUvoZzpkZuWCvGvU9ZFUaCqBW700umcKHdxg"
                            )

                            // Step 3: Create the PaymentSheet instance and handle the result callback
                            val paymentSheet = PaymentSheet.Builder { result ->
                                isPaying = false
                                when (result) {
                                    is PaymentSheetResult.Completed -> {
                                        status = "Paid"
                                        Toast.makeText(
                                            context,
                                            "Payment successful",
                                            Toast.LENGTH_SHORT
                                        ).show()
                                    }
                                    is PaymentSheetResult.Canceled -> {
                                        Toast.makeText(
                                            context,
                                            "Payment cancelled – stays pending",
                                            Toast.LENGTH_SHORT
                                        ).show()
                                    }
                                    is PaymentSheetResult.Failed -> {
                                        Toast.makeText(
                                            context,
                                            "Payment failed: ${result.error.message}",
                                            Toast.LENGTH_LONG
                                        ).show()
                                    }
                                }
                            }.build(context as ComponentActivity) // <-- Fixed: Added Activity argument

                            // Step 4: Present the sheet using the instance
                            paymentSheet.presentWithPaymentIntent(
                                paymentIntentClientSecret = clientSecret,
                                configuration = PaymentSheet.Configuration(
                                    merchantDisplayName = "AL Agentic Lender"
                                )
                            )
                        } catch (e: Exception) {
                            isPaying = false
                            Toast.makeText(
                                context,
                                "Could not create payment: ${e.message}. Check connection.",
                                Toast.LENGTH_LONG
                            ).show()
                        }
                    }
                },
                enabled = !isPaying,
                modifier = Modifier.fillMaxWidth().height(50.dp),
                colors = ButtonDefaults.buttonColors(containerColor = primaryColor)
            ) {
                if (isPaying) {
                    CircularProgressIndicator(
                        modifier = Modifier.size(20.dp),
                        color = Color.White,
                        strokeWidth = 2.dp
                    )
                } else {
                    Text("Pay €%.2f".format(amountCents / 100.0))
                }
            }
        }
    }
}


// =============================================================================
//  Loan Status — Firestore snapshot listener
// =============================================================================
private val STATUS_STEPS = listOf(
    "Applied", "AI Deliberated", "Underwriter Approved", "Funded", "Closed"
)

@Composable
fun LoanStatusScreen(
    navController: NavController,
    textColor: Color,
    primaryColor: Color,
    cardColor: Color
) {
    val applicationId = SessionState.currentApplicationId
    var loan by remember { mutableStateOf<LoanStatusView?>(null) }
    var error by remember { mutableStateOf<String?>(null) }
    var loading by remember { mutableStateOf(true) }

    LaunchedEffect(applicationId) {
        if (applicationId.isNullOrBlank()) {
            loading = false
            error = "No application"
            return@LaunchedEffect
        }
        val db = FirebaseFirestore.getInstance()
        val listener = db.collection("applications")
            .document(applicationId)
            .addSnapshotListener { snap, err ->
                loading = false
                if (err != null) {
                    error = "No connection"
                    return@addSnapshotListener
                }
                if (snap == null || !snap.exists()) {
                    error = "No application"
                    loan = null
                    return@addSnapshotListener
                }
                loan = LoanStatusView(
                    applicationId = applicationId,
                    ltv = (snap.getDouble("ltv") ?: 0.0),
                    dti = (snap.getDouble("dti") ?: 0.0),
                    approvalLikelihood = snap.getString("approvalLikelihood") ?: "Pending",
                    status = snap.getString("status") ?: "Applied",
                    declineReason = snap.getString("declineReason"),
                    transactionRef = snap.getString("transactionRef")
                )
            }
        // Keep listener alive until screen leaves composition
        try {
            while (true) { delay(600_000) }
        } finally {
            listener.remove()
        }
    }

    Column(
        modifier = Modifier.fillMaxSize().padding(16.dp).verticalScroll(rememberScrollState())
    ) {
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Text("My Loan", fontSize = 20.sp, fontWeight = FontWeight.Bold, color = textColor)
            IconButton(onClick = { isDarkMode = !isDarkMode }) {
                Icon(
                    imageVector = if (isDarkMode) Icons.Default.LightMode else Icons.Default.DarkMode,
                    contentDescription = "Toggle Theme",
                    tint = primaryColor
                )
            }
        }
        Text("Application #${applicationId ?: "—"}", fontSize = 12.sp, color = Color.Gray)

        Spacer(Modifier.height(16.dp))

        when {
            loading && loan == null -> Box(Modifier.fillMaxWidth(), contentAlignment = Alignment.Center) {
                CircularProgressIndicator(color = primaryColor)
            }

            error == "No application" -> {
                Text("You don't have an application yet.", color = textColor)
                Spacer(Modifier.height(8.dp))
                Button(
                    onClick = { navController.navigate("affordability") },
                    colors = ButtonDefaults.buttonColors(containerColor = primaryColor)
                ) { Text("Start Application") }
            }

            error == "No connection" && loan == null -> {
                Text("No connection. Retrying when online…", color = textColor)
            }

            loan != null -> {
                val l = loan!!

                Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                    StatTile("LTV", "${l.ltv.toInt()}%", primaryColor, cardColor, textColor, Modifier.weight(1f))
                    StatTile("DTI", "${l.dti}%", primaryColor, cardColor, textColor, Modifier.weight(1f))
                }
                Spacer(Modifier.height(16.dp))

                Card(
                    modifier = Modifier.fillMaxWidth(),
                    colors = CardDefaults.cardColors(containerColor = cardColor)
                ) {
                    Column(Modifier.padding(16.dp)) {
                        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                            Text("Approval Likelihood", color = textColor)
                            Text(l.approvalLikelihood, fontWeight = FontWeight.Bold, color = textColor)
                        }
                        Spacer(Modifier.height(8.dp))
                        val frac = when (l.approvalLikelihood) {
                            "High" -> 1f
                            "Medium" -> 0.6f
                            else -> 0.3f
                        }
                        LinearProgressIndicator(
                            progress = { frac },
                            modifier = Modifier.fillMaxWidth().height(10.dp).clip(RoundedCornerShape(5.dp)),
                            color = primaryColor,
                            trackColor = primaryColor.copy(alpha = 0.2f)
                        )
                    }
                }

                Spacer(Modifier.height(24.dp))
                Text("Status", fontWeight = FontWeight.Bold, color = textColor)
                Spacer(Modifier.height(8.dp))

                val currentIdx = STATUS_STEPS.indexOf(l.status).let { if (it == -1) 0 else it }
                STATUS_STEPS.forEachIndexed { idx, step ->
                    val done = idx <= currentIdx
                    val isCurrent = idx == currentIdx
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Box(
                            modifier = Modifier
                                .size(16.dp)
                                .clip(RoundedCornerShape(50))
                                .background(if (done) primaryColor else textColor.copy(alpha = 0.2f))
                        )
                        Spacer(Modifier.width(12.dp))
                        Text(
                            step,
                            color = textColor,
                            fontWeight = if (isCurrent) FontWeight.Bold else FontWeight.Normal
                        )
                    }
                    if (idx < STATUS_STEPS.lastIndex) {
                        Box(
                            modifier = Modifier
                                .padding(start = 7.dp)
                                .width(2.dp)
                                .height(20.dp)
                                .background(
                                    if (idx < currentIdx) primaryColor
                                    else textColor.copy(alpha = 0.2f)
                                )
                        )
                    }
                }

                if (l.status == "Declined" && !l.declineReason.isNullOrBlank()) {
                    Spacer(Modifier.height(12.dp))
                    Text("Reason: ${l.declineReason}", color = Color.Red)
                }

                Spacer(Modifier.height(24.dp))

                Card(
                    modifier = Modifier.fillMaxWidth(),
                    colors = CardDefaults.cardColors(containerColor = cardColor)
                ) {
                    Column(Modifier.padding(16.dp)) {
                        Text("Transaction reference", fontSize = 12.sp, color = Color.Gray)
                        if ((l.status == "Funded" || l.status == "Closed") && !l.transactionRef.isNullOrBlank()) {
                            Text(l.transactionRef, color = primaryColor, fontWeight = FontWeight.Bold)
                        } else {
                            Text("Shown once funded", color = Color.Gray)
                        }
                    }
                }
            }
        }

        Spacer(Modifier.height(16.dp))
        OutlinedButton(
            onClick = { navController.navigate("dashboard") },
            modifier = Modifier.fillMaxWidth()
        ) { Text("Back to Dashboard", color = textColor) }
    }
}

@Composable
private fun StatTile(
    label: String,
    value: String,
    primaryColor: Color,
    cardColor: Color,
    textColor: Color,
    modifier: Modifier = Modifier
) {
    Card(
        modifier = modifier,
        colors = CardDefaults.cardColors(containerColor = cardColor),
        elevation = CardDefaults.cardElevation(2.dp)
    ) {
        Column(
            modifier = Modifier.fillMaxWidth().padding(16.dp),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Text(label, fontSize = 12.sp, color = Color.Gray)
            Text(value, fontSize = 28.sp, fontWeight = FontWeight.Bold, color = primaryColor)
        }
    }
}

// =============================================================================
//  Placeholder
// =============================================================================
@Composable
fun PlaceholderScreen(
    navController: NavController,
    title: String,
    textColor: Color,
    primaryColor: Color
) {
    Column(
        modifier = Modifier.fillMaxSize(),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center
    ) {
        Text(title, fontSize = 22.sp, color = textColor)
        Spacer(Modifier.height(16.dp))
        Button(
            onClick = { navController.navigate("dashboard") },
            colors = ButtonDefaults.buttonColors(containerColor = primaryColor)
        ) { Text("Back to Dashboard") }
    }
}
