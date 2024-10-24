<?php
header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: POST, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type');

// Handle preflight requests
if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(200);
    exit();
}

// Check if it's a POST request
if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    http_response_code(405);
    echo json_encode(['error' => 'Method not allowed']);
    exit();
}

// Get and validate input
try {
    $input = json_decode(file_get_contents('php://input'), true);
    if (json_last_error() !== JSON_ERROR_NONE) {
        throw new Exception('Invalid JSON');
    }
} catch (Exception $e) {
    http_response_code(400);
    echo json_encode(['error' => 'Invalid request data']);
    exit();
}

// API Key configuration
$GEMINI_API_KEY = 'AIzaSyAJydXRggk-HP3BsgbtuCRuqbI6b8Xpw9w';
$MODEL = 'gemini-1.5-flash-002';

// Validate required fields
$question = $input['question'] ?? '';
$content = $input['content'] ?? '';
$url = $input['url'] ?? '';
$simplify = $input['simplify'] ?? false;

if (empty($question)) {
    http_response_code(400);
    echo json_encode(['error' => 'Question is required']);
    exit();
}

// Prepare the request prompt
$prompt = "Analyze the following and provide a clear answer focusing specifically on:
1. Policies and rules
2. Entitlements and benefits
3. Time periods, deadlines, and timing requirements
4. Costs, fees, and financial aspects

Format the response with:
- Use **bold** for all important information
- Organize using bullet points
- Group similar information together
- Be direct and specific
";

// Add simplification instructions if simplify is true
if ($simplify) {
    $prompt .= "
Please provide the response in very simple, easy-to-understand language:
- Use short, simple sentences
- Avoid technical terms and jargon
- Explain concepts as if speaking to someone with no background knowledge
- Use everyday examples where helpful
- Keep explanations straightforward and basic
- Break down complex ideas into simple steps
";
}

if (!empty($content)) {
    $prompt .= "\nContent: $content\n\n";
}

$prompt .= "Question: $question";

// Prepare the request to Gemini API
$apiUrl = "https://generativelanguage.googleapis.com/v1beta/models/$MODEL:generateContent?key=$GEMINI_API_KEY";

$requestData = [
    'contents' => [
        [
            'role' => 'user',
            'parts' => [
                [
                    'text' => $prompt
                ]
            ]
        ]
    ],
    'generationConfig' => [
        'temperature' => 0.1,
        'topP' => 0.8,
        'topK' => 40,
        'maxOutputTokens' => 1024
    ]
];

// Make the request to Gemini API
$ch = curl_init($apiUrl);
curl_setopt_array($ch, [
    CURLOPT_RETURNTRANSFER => true,
    CURLOPT_POST => true,
    CURLOPT_POSTFIELDS => json_encode($requestData),
    CURLOPT_HTTPHEADER => [
        'Content-Type: application/json'
    ]
]);

$response = curl_exec($ch);
$httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
$curlError = curl_errno($ch);
$curlErrorMessage = curl_error($ch);
curl_close($ch);

// Handle potential cURL errors
if ($curlError) {
    http_response_code(500);
    echo json_encode([
        'error' => 'Connection error',
        'details' => $curlErrorMessage
    ]);
    exit();
}

// Process the API response
if ($httpCode === 200) {
    $result = json_decode($response, true);
    
    if (isset($result['candidates'][0]['content']['parts'][0]['text'])) {
        $finalResponse = $result['candidates'][0]['content']['parts'][0]['text'];
        
        // Clean up the response
        $finalResponse = trim($finalResponse);
        $finalResponse = preg_replace('/\n{3,}/', "\n\n", $finalResponse);
        
        // Ensure important information is properly formatted
        $patterns = [
            // Time and dates
            '/(\d+\s*(?:days?|weeks?|months?|years?))/i',
            '/(\d{1,2}\/\d{1,2}\/\d{2,4})/',
            '/(\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4})/i',
            
            // Costs and money
            '/(\$\s*\d+(?:,\d{3})*(?:\.\d{2})?)/i',
            '/(\d+(?:,\d{3})*(?:\.\d{2})?\s*(?:dollars?|USD))/i',
            
            // Percentages
            '/(\d+(?:\.\d+)?%)/i',
            
            // Policy keywords
            '/(policy|requirement|regulation|rule|guideline):/i',
            
            // Entitlement keywords
            '/(entitled to|eligible for|qualify for|benefit):/i'
        ];
        
        foreach ($patterns as $pattern) {
            $finalResponse = preg_replace($pattern, '**$1**', $finalResponse);
        }
        
        // Ensure bullet points are consistent
        $finalResponse = preg_replace('/^[•·]\s*/m', '- ', $finalResponse);
        
        echo json_encode([
            'response' => $finalResponse,
            'status' => 'success'
        ]);
    } else {
        http_response_code(500);
        echo json_encode([
            'error' => 'Invalid API response structure',
            'details' => $result
        ]);
    }
} else {
    // Log the error response
    error_log("Gemini API Error: " . $response);
    
    http_response_code($httpCode);
    echo json_encode([
        'error' => 'API Error',
        'details' => json_decode($response, true),
        'httpCode' => $httpCode
    ]);
}
?>
