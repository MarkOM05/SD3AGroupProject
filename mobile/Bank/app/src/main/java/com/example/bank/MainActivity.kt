package com.example.bank

import android.R.attr.textColor
import android.os.Bundle
import android.widget.Toast
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
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
import androidx.core.view.WindowCompat.enableEdgeToEdge
import androidx.navigation.NavController
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import com.example.bank.ui.theme.BankTheme
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import retrofit2.http.Body
import retrofit2.http.POST
import androidx.compose.runtime.rememberCoroutineScope
import kotlinx.coroutines.launch

data class LoanRequest(
    val income: Double,
    val debt: Double,
    val deposit: Double,
    val term: Int
)

data class LoanResponse(
    val ltv: Double,
    val dti: Double,
    val approvalLikelihood: String)

interface BankApi {
    @POST(BASE_URL + "calculate")
    suspend fun calculateLoan(@Body request: LoanRequest): LoanResponse
}

object RetrofitClient {
    private const val BASE_URL = "https://sd3agroupproject.onrender.com/"

    val api: BankApi by lazy {
        Retrofit.Builder()
            .baseUrl(BASE_URL)
            .addConverterFactory(GsonConverterFactory.create())
            .build()
            .create(BankApi::class.java)
    }
}

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContent {
            BankTheme {
                MainApp()
            }
        }
    }
}

// Global state for Dark Mode (simple and effective)
var isDarkMode by mutableStateOf(false)

@Composable
fun MainApp() {
    val navController = rememberNavController()

    // Theme colors based on the toggle
    val backgroundColor = if (isDarkMode) Color(0xFF121212) else Color(0xFFF7F8FA)
    val textColor = if (isDarkMode) Color.White else Color.Black
    val primaryColor = if (isDarkMode) Color(0xFFFFD100) else Color(0xFF003366) // Gold in dark, Navy in light
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
                composable("login") { LoginScreen(navController, textColor, primaryColor, cardColor) }
                composable("dashboard") { DashboardScreen(navController, textColor, primaryColor, cardColor) }
                composable("affordability") { Affordability(navController, "Affordability & Loan Application", textColor, primaryColor, cardColor) }
                composable("property_checker") { PlaceholderScreen(navController, "Fair-Price Property Checker", textColor, primaryColor) }
                composable("status") { PlaceholderScreen(navController, "AL-AI Status", textColor, primaryColor) }
                composable("contact") { PlaceholderScreen(navController, "Broker / Official Contact", textColor, primaryColor) }
                composable("payments") { PlaceholderScreen(navController, "Payments", textColor, primaryColor) }
                composable("support") { PlaceholderScreen(navController, "Support & Reviews", textColor, primaryColor) }
            }
        }
    }
}

data class DashboardItem(
    val id: Int,
    val label: String,
    val route: String,
    val icon: ImageVector
)

// --- LOGIN SCREEN ---
@Composable
fun LoginScreen(
    navController: NavController,
    textColor: Color,
    primaryColor: Color,
    cardColor: Color
) {
    var email by remember { mutableStateOf("") }
    var password by remember { mutableStateOf("") }
    val context = LocalContext.current

    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(24.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center
    ) {
        // Dark Mode Toggle at top right
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.End
        ) {
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

        Spacer(modifier = Modifier.height(16.dp))

        Text(
            text = "AL Agentic Lender",
            fontSize = 28.sp,
            fontWeight = FontWeight.Bold,
            color = textColor
        )

        Spacer(modifier = Modifier.height(32.dp))

        OutlinedTextField(
            value = email,
            onValueChange = { email = it },
            label = { Text("Email") },
            modifier = Modifier.fillMaxWidth()
        )
        Spacer(modifier = Modifier.height(16.dp))

        OutlinedTextField(
            value = password,
            onValueChange = { password = it },
            label = { Text("Password") },
            visualTransformation = PasswordVisualTransformation(),
            modifier = Modifier.fillMaxWidth()
        )

        Spacer(modifier = Modifier.height(24.dp))

        Button(
            onClick = {
                if (email.isNotBlank() && password.isNotBlank()) {
                    Toast.makeText(context, "Login Successful", Toast.LENGTH_SHORT).show()
                    navController.navigate("dashboard") {
                        popUpTo("login") { inclusive = true }
                    }
                } else {
                    Toast.makeText(context, "Please enter details", Toast.LENGTH_SHORT).show()
                }
            },
            colors = ButtonDefaults.buttonColors(containerColor = primaryColor),
            modifier = Modifier
                .fillMaxWidth()
                .height(50.dp)
        ) {
            Text("Login")
        }
    }
}

// --- DASHBOARD SCREEN ---
@Composable
fun DashboardScreen(
    navController: NavController,
    textColor: Color,
    primaryColor: Color,
    cardColor: Color
) {
    val context = LocalContext.current
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
            Text(
                text = "Dashboard",
                fontSize = 24.sp,
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

        Spacer(modifier = Modifier.height(16.dp))

        LazyColumn(
            modifier = Modifier.fillMaxSize(),
            verticalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            items(items, key = { it.id }) { item ->
                DashboardRow(
                    item = item,
                    cardColor = cardColor,
                    textColor = textColor,
                    onClick = {
                        navController.navigate(item.route)
                    }
                )
            }
        }
    }
}

@Composable
fun DashboardRow(
    item: DashboardItem,
    cardColor: Color,
    textColor: Color,
    onClick: () -> Unit
) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(8.dp))
            .clickable { onClick() }
            .padding(16.dp),
        verticalAlignment = Alignment.CenterVertically
    ) {
        Icon(
            imageVector = item.icon,
            contentDescription = null,
            tint = textColor,
            modifier = Modifier.size(24.dp)
        )
        Spacer(modifier = Modifier.width(16.dp))
        Text(
            text = item.label,
            fontSize = 16.sp,
            color = textColor
        )
    }
}

// --- AFFORDABILITY SCREEN ---
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
    var term by remember { mutableStateOf("30") }

    var isLoading by remember { mutableStateOf(false) }
    var ltvResult by remember { mutableStateOf<Double?>(null) }
    var dtiResult by remember { mutableStateOf<Double?>(null) }
    var approvalResult by remember { mutableStateOf("") }

    val context = LocalContext.current
    val coroutineScope = rememberCoroutineScope()

    val incomeDouble = income.toDoubleOrNull() ?: 0.0
    val debtDouble = debt.toDoubleOrNull() ?: 0.0
    val depositDouble = deposit.toDoubleOrNull() ?: 0.0
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
            Text(text = title, fontSize = 20.sp, fontWeight = FontWeight.Bold, color = textColor)
            IconButton(onClick = { isDarkMode = !isDarkMode }) {
                Icon(
                    imageVector = if (isDarkMode) Icons.Default.LightMode else Icons.Default.DarkMode,
                    contentDescription = "Toggle Theme",
                    tint = primaryColor
                )
            }
        }

        Spacer(modifier = Modifier.height(16.dp))

        OutlinedTextField(
            value = income,
            onValueChange = { income = it },
            label = { Text("Gross Income (€)") },
            keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
            modifier = Modifier.fillMaxWidth()
        )
        Spacer(modifier = Modifier.height(8.dp))

        OutlinedTextField(
            value = debt,
            onValueChange = { debt = it },
            label = { Text("Existing Debt (€)") },
            keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
            modifier = Modifier.fillMaxWidth()
        )
        Spacer(modifier = Modifier.height(8.dp))

        OutlinedTextField(
            value = deposit,
            onValueChange = { deposit = it },
            label = { Text("Deposit (€)") },
            keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
            modifier = Modifier.fillMaxWidth()
        )
        Spacer(modifier = Modifier.height(8.dp))

        OutlinedTextField(
            value = term,
            onValueChange = { term = it },
            label = { Text("Mortgage Term (Years)") },
            keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
            modifier = Modifier.fillMaxWidth()
        )

        Spacer(modifier = Modifier.height(24.dp))

        if (isLoading) {
            Box(modifier = Modifier.fillMaxWidth(), contentAlignment = Alignment.Center) {
                CircularProgressIndicator(color = primaryColor)
            }
        } else if (ltvResult != null && dtiResult != null) {
            Card(
                modifier = Modifier.fillMaxWidth(),
                colors = CardDefaults.cardColors(containerColor = cardColor),
                elevation = CardDefaults.cardElevation(defaultElevation = 4.dp)
            ) {
                Column(modifier = Modifier.padding(16.dp)){
                    Text("AI API Results", fontWeight = FontWeight.Bold, color = textColor)
                    Spacer(modifier = Modifier.height(8.dp))
                    Text("Approval: $approvalResult", color = primaryColor, fontWeight = FontWeight.Bold)
                    Spacer(modifier = Modifier.height(8.dp))
                    Text(
                        text = "LTV: ${String.format("%.1f", ltvResult)}%",
                        color = if (ltvResult!! > 90) Color.Red else primaryColor,
                        fontWeight = FontWeight.Bold
                    )
                    Text(
                        text = "DTI: ${String.format("%.1f", dtiResult)}%",
                        color = if (dtiResult!! > 40) Color.Red else primaryColor,
                        fontWeight = FontWeight.Bold
                    )
                }
            }
        }

        Spacer(modifier = Modifier.height(24.dp))

        Button(
            onClick = {
                // Call the API here using Coroutines
                coroutineScope.launch {
                    isLoading = true
                    try {
                        val request = LoanRequest(incomeDouble, debtDouble, depositDouble, termInt)
                        val response = RetrofitClient.api.calculateLoan(request)

                        // Update the UI with the real API data
                        ltvResult = response.ltv
                        dtiResult = response.dti
                        approvalResult = response.approvalLikelihood

                        Toast.makeText(context, "API Call Successful!", Toast.LENGTH_SHORT).show()
                    } catch (e: Exception) {
                        Toast.makeText(context, "API Error: ${e.message}", Toast.LENGTH_LONG).show()
                    } finally {
                        isLoading = false
                    }
                }
            },
            modifier = Modifier.fillMaxWidth(),
            colors = ButtonDefaults.buttonColors(containerColor = primaryColor),
            enabled = incomeDouble > 0 && depositDouble > 0 && !isLoading
        ) {
            Text("Submit to AI API")
        }

        Spacer(modifier = Modifier.height(8.dp))
        OutlinedButton(
            onClick = { navController.navigate("dashboard") },
            modifier = Modifier.fillMaxWidth()
        ) {
            Text("Back to Dashboard", color = textColor)
        }
    }
}
// --- PLACEHOLDER SCREEN ---
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
        Text(text = title, fontSize = 22.sp, color = textColor)
        Spacer(modifier = Modifier.height(16.dp))
        Button(
            onClick = { navController.navigate("dashboard") },
            colors = ButtonDefaults.buttonColors(containerColor = primaryColor)
        ) {
            Text(text = "Back to Dashboard")
        }
    }
}
