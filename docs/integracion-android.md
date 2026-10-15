# Integración Android — Test Flow API v2

**Fecha de actualización:** 2026-10-14  
**URL Base de la API:** `https://8cspr7pmca.execute-api.us-east-1.amazonaws.com/` *(en Retrofit la URL base siempre debe terminar con barra `/`)*  
**Contrato OpenAPI v2:** [`docs/openapi.json`](openapi.json) (versión 2.0.0)

---

## 1. Resumen de Cambios (Migración v1 a v2)

1. **Autenticación obligatoria con Bearer Token:**
   - Todas las consultas de datos (`/v1/me/...`) ahora exigen la cabecera `Authorization: Bearer <access_token>`.
   - El token es una cadena opaca de 256 bits (no es un JWT), con expiración de **7200 segundos (2 horas)**. No tiene refresh token; al expirar se debe solicitar nuevo inicio de sesión.
2. **Eliminación del selector público de usuarios:**
   - La ruta antigua `GET /v1/demo/users` ya no devuelve un directorio público (responderá HTTP 401 si se invoca sin sesión).
   - El selector de usuarios en `AuthScreen.kt` se reemplaza por formularios reales de **Iniciar Sesión** y **Registro**.
3. **Rutas canónicas `/v1/me/...` sin `user_id` en la URL:**
   - El backend identifica al usuario a partir del token de sesión. Ya no se debe enviar el `userId` en la ruta de las peticiones (usar `/v1/me/dashboard`, `/v1/me/incomes`, etc.).
4. **Modelo de Usuario / Perfil:**
   - Se reemplaza `DemoUser` por `ProfileDto`:
     - Incluye `email` (String).
     - `ultimo_digito_ruc` es `Int?` (nullable), ya que para usuarios recién registrados nace en `null`.
     - Se retira el campo `es_ficticio`.
5. **Requisito en peticiones POST:**
   - Todo `POST` (incluido `/v1/auth/logout`) exige cabecera `Content-Type: application/json` y un cuerpo JSON válido (para logout se envía un objeto vacío `{}`).
6. **Políticas de tasa y throttling:**
   - Throttling en API Gateway: 2 req/s con ráfaga de 5 reqs. Mantener reintento con retroceso exponencial ante HTTP 429.

---

## 2. Matriz de Endpoints

| Método | Ruta | Requiere Sesión | Request Body | Respuesta HTTP 200 |
|---|---|:---:|---|---|
| `POST` | `v1/auth/register` | No | `{"nombre", "email", "password"}` | `SessionResponse` |
| `POST` | `v1/auth/login` | No | `{"email", "password"}` | `SessionResponse` |
| `POST` | `v1/auth/logout` | Sí | `{}` *(objeto JSON vacío)* | `{"ok": true}` |
| `GET`  | `v1/me` | Sí | *Sin cuerpo* | `ProfileDto` |
| `GET`  | `v1/me/dashboard` | Sí | *Params:* `anio=2026`, `mes=1..12` | `DashboardResponse` |
| `GET`  | `v1/me/incomes` | Sí | *Params opcionales:* `desde`, `hasta`, `q`, `cliente`, `estado` | `IncomeListResponse` |
| `GET`  | `v1/me/incomes/{id}` | Sí | *Path:* `id` del ingreso | `IncomeDto` |
| `GET`  | `v1/me/expenses` | Sí | *Params opcionales:* `desde`, `hasta`, `categoria`, `estado` | `ExpenseListResponse` |
| `GET`  | `v1/me/expenses/{id}`| Sí | *Path:* `id` del gasto | `ExpenseDto` |
| `GET`  | `v1/me/calendar` | Sí | *Params:* `anio=2026` | `CalendarItemListResponse` |
| `GET`  | `v1/me/notifications`| Sí | *Sin cuerpo* | `NotificationListResponse` |
| `POST` | `v1/me/simulations` | Sí | `IncomeSimulationRequest` o `ExpenseSimulationRequest` | `SimulationResultDto` |

---

## 3. Modelos Kotlin (`ApiModels.kt`)

Sustituir o complementar las definiciones en `app/src/main/java/com/gmaldonado/taxflow_movil/data/remote/models/ApiModels.kt`:

```kotlin
package com.gmaldonado.taxflow_movil.data.remote.models

import com.google.gson.annotations.SerializedName

// ── AUTENTICACIÓN Y SESIÓN ───────────────────────────────────────────────────

data class LoginRequest(
    @SerializedName("email") val email: String,
    @SerializedName("password") val password: String
)

data class RegisterRequest(
    @SerializedName("nombre") val nombre: String,
    @SerializedName("email") val email: String,
    @SerializedName("password") val password: String
)

data class ProfileDto(
    @SerializedName("id") val id: String,
    @SerializedName("nombre") val nombre: String,
    @SerializedName("email") val email: String,
    @SerializedName("profesion") val profesion: String,
    @SerializedName("ultimo_digito_ruc") val ultimoDigitoRuc: Int? // Nullable para cuentas nuevas
)

data class SessionResponse(
    @SerializedName("access_token") val accessToken: String,
    @SerializedName("token_type") val tokenType: String, // "Bearer"
    @SerializedName("expires_in") val expiresIn: Int,     // 7200 segundos
    @SerializedName("user") val user: ProfileDto
)

data class LogoutResponse(
    @SerializedName("ok") val ok: Boolean
)

// ── DASHBOARD ────────────────────────────────────────────────────────────────

data class RecentActivityDto(
    @SerializedName("tipo") val tipo: String, // "INGRESO" | "GASTO"
    @SerializedName("id") val id: String,
    @SerializedName("fecha") val fecha: String,
    @SerializedName("titulo") val titulo: String,
    @SerializedName("monto_centimos") val montoCentimos: Long
)

data class DashboardResponse(
    @SerializedName("usuario_id") val usuarioId: String,
    @SerializedName("anio") val anio: Int,
    @SerializedName("mes") val mes: Int,
    @SerializedName("ingresos_mes_centimos") val ingresosMesCentimos: Long,
    @SerializedName("ingresos_anio_centimos") val ingresosAnioCentimos: Long,
    @SerializedName("retenciones_anio_centimos") val retencionesAnioCentimos: Long,
    @SerializedName("gastos_anio_centimos") val gastosAnioCentimos: Long,
    @SerializedName("deducible_anio_centimos") val deducibleAnioCentimos: Long,
    @SerializedName("limite_7_uit_centimos") val limite7UitCentimos: Long,
    @SerializedName("limite_3_uit_centimos") val limite3UitCentimos: Long,
    @SerializedName("reglas_version") val reglasVersion: String,
    @SerializedName("actividad_reciente") val actividadReciente: List<RecentActivityDto>
)

// ── INGRESOS ─────────────────────────────────────────────────────────────────

data class IncomeDto(
    @SerializedName("id") val id: String,
    @SerializedName("cliente") val cliente: String,
    @SerializedName("serie") val serie: String,
    @SerializedName("numero") val numero: String,
    @SerializedName("fecha") val fecha: String,
    @SerializedName("monto_bruto_centimos") val montoBrutoCentimos: Long,
    @SerializedName("retencion_centimos") val retencionCentimos: Long,
    @SerializedName("monto_neto_centimos") val montoNetoCentimos: Long,
    @SerializedName("estado") val estado: String, // "PAGADO" | "PENDIENTE" | "REVERTIDO"
    @SerializedName("origen") val origen: String
)

data class IncomeResumenDto(
    @SerializedName("bruto_centimos") val brutoCentimos: Long,
    @SerializedName("retencion_centimos") val retencionCentimos: Long,
    @SerializedName("neto_centimos") val netoCentimos: Long
)

data class IncomeListResponse(
    @SerializedName("items") val items: List<IncomeDto>,
    @SerializedName("total") val total: Int,
    @SerializedName("resumen") val resumen: IncomeResumenDto
)

// ── GASTOS ───────────────────────────────────────────────────────────────────

data class ExpenseDto(
    @SerializedName("id") val id: String,
    @SerializedName("proveedor") val proveedor: String,
    @SerializedName("serie") val serie: String,
    @SerializedName("numero") val numero: String,
    @SerializedName("fecha") val fecha: String,
    @SerializedName("categoria") val categoria: String, // "restaurantes" | "servicios" | "alojamiento" | "essalud"
    @SerializedName("monto_centimos") val montoCentimos: Long,
    @SerializedName("porcentaje_deducible_pb") val porcentajeDeduciblePb: Int,
    @SerializedName("deducible_centimos") val deducibleCentimos: Long,
    @SerializedName("estado") val estado: String, // "MANUAL" | "OBSERVADO"
    @SerializedName("origen") val origen: String
)

data class ExpenseResumenDto(
    @SerializedName("total_centimos") val totalCentimos: Long,
    @SerializedName("deducible_centimos") val deducibleCentimos: Long
)

data class ExpenseListResponse(
    @SerializedName("items") val items: List<ExpenseDto>,
    @SerializedName("total") val total: Int,
    @SerializedName("resumen") val resumen: ExpenseResumenDto
)

// ── CALENDARIO SUNAT ─────────────────────────────────────────────────────────

data class CalendarItemDto(
    @SerializedName("id") val id: String,
    @SerializedName("titulo") val titulo: String,
    @SerializedName("fecha") val fecha: String,
    @SerializedName("formulario") val formulario: String,
    @SerializedName("estado") val estado: String, // "PENDIENTE" | "PRESENTADO" | "ACTIVO"
    @SerializedName("detalle") val detalle: String,
    @SerializedName("origen") val origen: String
)

data class CalendarItemListResponse(
    @SerializedName("items") val items: List<CalendarItemDto>,
    @SerializedName("total") val total: Int
)

// ── NOTIFICACIONES ───────────────────────────────────────────────────────────

data class NotificationDto(
    @SerializedName("id") val id: String,
    @SerializedName("titulo") val titulo: String,
    @SerializedName("mensaje") val mensaje: String,
    @SerializedName("created_at") val createdAt: String,
    @SerializedName("es_urgente") val esUrgente: Boolean,
    @SerializedName("origen") val origen: String
)

data class NotificationListResponse(
    @SerializedName("items") val items: List<NotificationDto>,
    @SerializedName("total") val total: Int
)

// ── SIMULADOR TRIBUTARIO ─────────────────────────────────────────────────────

data class IncomeSimulationRequest(
    @SerializedName("tipo") val tipo: String = "INGRESO",
    @SerializedName("monto_centimos") val montoCentimos: Long,
    @SerializedName("aplicar_retencion") val aplicarRetencion: Boolean
)

data class ExpenseSimulationRequest(
    @SerializedName("tipo") val tipo: String = "GASTO",
    @SerializedName("monto_centimos") val montoCentimos: Long,
    @SerializedName("categoria") val categoria: String
)

data class SimulationResultDto(
    @SerializedName("tipo") val tipo: String,
    @SerializedName("monto_centimos") val montoCentimos: Long,
    @SerializedName("retencion_centimos") val retencionCentimos: Long,
    @SerializedName("neto_centimos") val netoCentimos: Long,
    @SerializedName("deducible_centimos") val deducibleCentimos: Long,
    @SerializedName("reglas_version") val reglasVersion: String,
    @SerializedName("persistido") val persistido: Boolean
)

// ── RESPUESTA DE ERROR DEL BACKEND ───────────────────────────────────────────

data class ApiErrorDetail(
    @SerializedName("code") val code: String,
    @SerializedName("message") val message: String,
    @SerializedName("request_id") val requestId: String
)

data class ApiErrorResponse(
    @SerializedName("error") val error: ApiErrorDetail
)
```

---

## 4. Interfaz de Servicio Retrofit (`TaxflowApiService.kt`)

Actualizar `app/src/main/java/com/gmaldonado/taxflow_movil/data/remote/TaxflowApiService.kt`:

```kotlin
package com.gmaldonado.taxflow_movil.data.remote

import com.gmaldonado.taxflow_movil.data.remote.models.*
import retrofit2.http.*

interface TaxflowApiService {

    // ── AUTENTICACIÓN ────────────────────────────────────────────────────────

    @POST("v1/auth/register")
    suspend fun register(
        @Body request: RegisterRequest
    ): SessionResponse

    @POST("v1/auth/login")
    suspend fun login(
        @Body request: LoginRequest
    ): SessionResponse

    @POST("v1/auth/logout")
    suspend fun logout(
        @Body emptyBody: Map<String, String> = emptyMap() // Requiere cuerpo JSON {}
    ): LogoutResponse

    @GET("v1/me")
    suspend fun getProfile(): ProfileDto

    // ── RECURSOS DEL USUARIO AUTENTICADO (/v1/me) ───────────────────────────

    @GET("v1/me/dashboard")
    suspend fun getDashboard(
        @Query("anio") anio: Int = 2026,
        @Query("mes") mes: Int = 9
    ): DashboardResponse

    @GET("v1/me/incomes")
    suspend fun getIncomes(
        @Query("desde") desde: String? = null,
        @Query("hasta") hasta: String? = null,
        @Query("q") q: String? = null,
        @Query("cliente") cliente: String? = null,
        @Query("estado") estado: String? = null
    ): IncomeListResponse

    @GET("v1/me/incomes/{id}")
    suspend fun getIncomeDetail(
        @Path("id") id: String
    ): IncomeDto

    @GET("v1/me/expenses")
    suspend fun getExpenses(
        @Query("desde") desde: String? = null,
        @Query("hasta") hasta: String? = null,
        @Query("categoria") categoria: String? = null,
        @Query("estado") estado: String? = null
    ): ExpenseListResponse

    @GET("v1/me/expenses/{id}")
    suspend fun getExpenseDetail(
        @Path("id") id: String
    ): ExpenseDto

    @GET("v1/me/calendar")
    suspend fun getCalendar(
        @Query("anio") anio: Int = 2026
    ): CalendarItemListResponse

    @GET("v1/me/notifications")
    suspend fun getNotifications(): NotificationListResponse

    @POST("v1/me/simulations")
    suspend fun simulateIncome(
        @Body request: IncomeSimulationRequest
    ): SimulationResultDto

    @POST("v1/me/simulations")
    suspend fun simulateExpense(
        @Body request: ExpenseSimulationRequest
    ): SimulationResultDto
}
```

---

## 5. Cliente HTTP y AuthInterceptor (`ApiClient.kt`)

Actualizar `app/src/main/java/com/gmaldonado/taxflow_movil/data/remote/ApiClient.kt` para adjuntar automáticamente el token Bearer:

```kotlin
package com.gmaldonado.taxflow_movil.data.remote

import com.gmaldonado.taxflow_movil.data.repository.TaxflowRepository
import okhttp3.Interceptor
import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import java.util.concurrent.TimeUnit

object ApiClient {
    private const val BASE_URL = "https://8cspr7pmca.execute-api.us-east-1.amazonaws.com/"

    // Inyecta Authorization: Bearer <token> si hay sesión activa
    private val authInterceptor = Interceptor { chain ->
        val original = chain.request()
        val token = TaxflowRepository.getAuthToken()
        val builder = original.newBuilder()

        if (!token.isNullOrBlank()) {
            builder.header("Authorization", "Bearer $token")
        }

        chain.proceed(builder.build())
    }

    // Rate limiting interceptor con retroceso exponencial ante HTTP 429
    private val rateLimitRetryInterceptor = Interceptor { chain ->
        var response = chain.proceed(chain.request())
        var attempt = 0
        val maxRetries = 3

        while (response.code == 429 && attempt < maxRetries) {
            attempt++
            response.close()
            val backoffMs = (500L * (1 shl (attempt - 1))) // 500ms, 1000ms, 2000ms
            try {
                Thread.sleep(backoffMs)
            } catch (_: InterruptedException) {}
            response = chain.proceed(chain.request())
        }
        response
    }

    private val okHttpClient: OkHttpClient by lazy {
        // En producción/demo, evitar registrar tokens o contraseñas en los logs
        val logging = HttpLoggingInterceptor().apply {
            level = HttpLoggingInterceptor.Level.BASIC
        }

        OkHttpClient.Builder()
            .addInterceptor(authInterceptor)
            .addInterceptor(rateLimitRetryInterceptor)
            .addInterceptor(logging)
            .connectTimeout(15, TimeUnit.SECONDS)
            .readTimeout(15, TimeUnit.SECONDS)
            .writeTimeout(15, TimeUnit.SECONDS)
            .build()
    }

    private val retrofit: Retrofit by lazy {
        Retrofit.Builder()
            .baseUrl(BASE_URL)
            .client(okHttpClient)
            .addConverterFactory(GsonConverterFactory.create())
            .build()
    }

    val service: TaxflowApiService by lazy {
        retrofit.create(TaxflowApiService::class.java)
    }
}
```

---

## 6. Lógica de Repositorio y Sesión (`TaxflowRepository.kt`)

Actualizar `TaxflowRepository.kt` para centralizar la sesión:

```kotlin
package com.gmaldonado.taxflow_movil.data.repository

import com.gmaldonado.taxflow_movil.data.remote.ApiClient
import com.gmaldonado.taxflow_movil.data.remote.models.*
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow

object TaxflowRepository {
    private val api = ApiClient.service

    private var _authToken: String? = null
    fun getAuthToken(): String? = _authToken

    private val _currentUser = MutableStateFlow<ProfileDto?>(null)
    val currentUser: StateFlow<ProfileDto?> = _currentUser.asStateFlow()

    fun isLoggedIn(): Boolean = !_authToken.isNullOrBlank()

    // ── AUTENTICACIÓN ────────────────────────────────────────────────────────

    suspend fun login(email: String, pass: String): Result<ProfileDto> {
        return try {
            val res = api.login(LoginRequest(email.trim().lowercase(), pass))
            _authToken = res.accessToken
            _currentUser.value = res.user
            Result.success(res.user)
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    suspend fun register(nombre: String, email: String, pass: String): Result<ProfileDto> {
        return try {
            val res = api.register(RegisterRequest(nombre.trim(), email.trim().lowercase(), pass))
            _authToken = res.accessToken
            _currentUser.value = res.user
            Result.success(res.user)
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    suspend fun logout(): Result<Boolean> {
        return try {
            if (isLoggedIn()) {
                api.logout()
            }
            clearSession()
            Result.success(true)
        } catch (e: Exception) {
            clearSession()
            Result.failure(e)
        }
    }

    fun clearSession() {
        _authToken = null
        _currentUser.value = null
    }

    // ── DATOS DE CUENTA (/v1/me) ─────────────────────────────────────────────

    suspend fun getProfile(): Result<ProfileDto> {
        return try {
            val res = api.getProfile()
            _currentUser.value = res
            Result.success(res)
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    suspend fun getDashboard(anio: Int = 2026, mes: Int = 9): Result<DashboardResponse> {
        return try {
            val res = api.getDashboard(anio = anio, mes = mes)
            Result.success(res)
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    suspend fun getIncomes(
        desde: String? = null,
        hasta: String? = null,
        q: String? = null,
        cliente: String? = null,
        estado: String? = null
    ): Result<IncomeListResponse> {
        return try {
            val res = api.getIncomes(desde, hasta, q, cliente, estado)
            Result.success(res)
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    suspend fun getIncomeDetail(id: String): Result<IncomeDto> {
        return try {
            val res = api.getIncomeDetail(id)
            Result.success(res)
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    suspend fun getExpenses(
        desde: String? = null,
        hasta: String? = null,
        categoria: String? = null,
        estado: String? = null
    ): Result<ExpenseListResponse> {
        return try {
            val res = api.getExpenses(desde, hasta, categoria, estado)
            Result.success(res)
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    suspend fun getExpenseDetail(id: String): Result<ExpenseDto> {
        return try {
            val res = api.getExpenseDetail(id)
            Result.success(res)
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    suspend fun getCalendar(anio: Int = 2026): Result<CalendarItemListResponse> {
        return try {
            val res = api.getCalendar(anio = anio)
            Result.success(res)
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    suspend fun getNotifications(): Result<NotificationListResponse> {
        return try {
            val res = api.getNotifications()
            Result.success(res)
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    suspend fun simulateIncome(montoCentimos: Long, aplicarRetencion: Boolean): Result<SimulationResultDto> {
        return try {
            val res = api.simulateIncome(IncomeSimulationRequest(montoCentimos = montoCentimos, aplicarRetencion = aplicarRetencion))
            Result.success(res)
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    suspend fun simulateExpense(montoCentimos: Long, categoria: String): Result<SimulationResultDto> {
        return try {
            val res = api.simulateExpense(ExpenseSimulationRequest(montoCentimos = montoCentimos, categoria = categoria))
            Result.success(res)
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
}
```

---

## 7. Formulario de Autenticación (`AuthScreen.kt`)

En `AuthScreen.kt`:
1. Reemplazar la lista `demoUsers` y la llamada a `fetchDemoUsers()` por dos pestañas: **"Iniciar Sesión"** y **"Registrarse"**.
2. **Validaciones en cliente:**
   - **Email:** debe ser una dirección válida (máximo 100 caracteres).
   - **Contraseña:** longitud estricta de **12 a 128 caracteres**. (No usar contraseñas cortas o el backend devolverá `400 VALIDATION_ERROR`).
   - **Nombre (solo registro):** longitud de 2 a 150 caracteres.
3. **Mapeo de Errores HTTP:**
   - `HTTP 401` con código `INVALID_CREDENTIALS` → Mostrar: *"Correo o contraseña incorrectos"*.
   - `HTTP 409` con código `EMAIL_ALREADY_EXISTS` → Mostrar: *"El correo ya se encuentra registrado"*.
   - `HTTP 400` con código `VALIDATION_ERROR` → Mostrar: *"Verifique los datos ingresados (la contraseña debe tener mínimo 12 caracteres)"*.
   - `HTTP 429` → Reintentos automáticos mediante el interceptor.

---

## 8. Cuentas de Prueba Pre-cargadas vs Cuentas Nuevas

- **Cuentas Pre-cargadas para Pruebas Académicas:**
  Existen 3 cuentas con datos iniciales (Carlos Jara, Carmen González y Óscar Paredes), cada una con 15 ingresos y 15 gastos. Sus credenciales se encuentran en el archivo local `C:\Github\Taxflow_DB\private\accesos-prueba.txt` *(archivo confidencial excluido de Git)*.
- **Cuentas Nuevas Creadas con Registro:**
  Nacen completamente limpias. El `Dashboard` reportará valores en 0 y las listas de ingresos/gastos devolverán `items: []`. La aplicación Android debe mostrar `EmptyStates` ordenados sin asumir datos preexistentes.

---

## 9. Checklist de Verificación de Integración

- [ ] `ApiClient.kt` incluye el `AuthInterceptor` para inyectar `Authorization: Bearer <token>`.
- [ ] `POST /v1/auth/logout` envía un cuerpo JSON `{}` (`emptyMap()`).
- [ ] `ProfileDto` tiene `ultimoDigitoRuc` como `Int?` (nullable) y se eliminó la dependencia de `esFicticio`.
- [ ] Todas las llamadas a recursos usan rutas `/v1/me/...` sin `userId` en el path.
- [ ] Al recibir un error `401` en cualquier pantalla, la app limpia la sesión y regresa a `AuthScreen`.
