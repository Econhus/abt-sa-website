<?php
header('Content-Type: application/json; charset=utf-8');

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    http_response_code(405);
    echo json_encode(['success' => false, 'error' => 'method_not_allowed']);
    exit;
}

function clean($v) {
    $v = trim((string)($v ?? ''));
    $v = str_replace(["\r", "\n"], ' ', $v);
    return $v;
}

// Honeypot spam trap (hidden field real users never fill)
$honeypot = clean($_POST['website'] ?? '');
if ($honeypot !== '') {
    echo json_encode(['success' => true]);
    exit;
}

$name    = clean($_POST['name'] ?? '');
$phone   = clean($_POST['phone'] ?? '');
$email   = clean($_POST['email'] ?? '');
$service = clean($_POST['service'] ?? '');
$message = trim((string)($_POST['message'] ?? ''));
$message = str_replace("\r\n", "\n", $message);

$errors = [];
if ($name === '' || mb_strlen($name) < 2) $errors[] = 'name';
if ($phone === '' || !preg_match('/^[0-9+\s()\-]{7,20}$/', $phone)) $errors[] = 'phone';
if ($message === '' || mb_strlen($message) < 5) $errors[] = 'message';
if ($email !== '' && !filter_var($email, FILTER_VALIDATE_EMAIL)) $errors[] = 'email';
if (mb_strlen($name) > 100) $errors[] = 'name';
if (mb_strlen($message) > 4000) $errors[] = 'message';

if (!empty($errors)) {
    http_response_code(422);
    echo json_encode(['success' => false, 'error' => 'validation', 'fields' => array_values(array_unique($errors))]);
    exit;
}

$to = 'info@abt-sa.com';
$subject = '=?UTF-8?B?' . base64_encode('رسالة جديدة من نموذج التواصل - موقع ABT') . '?=';

$body  = "رسالة جديدة من نموذج التواصل بموقع abt-sa.com:\n\n";
$body .= "الاسم: $name\n";
$body .= "الجوال: $phone\n";
if ($email !== '') $body .= "البريد الإلكتروني: $email\n";
if ($service !== '') $body .= "الخدمة المطلوبة: $service\n";
$body .= "\nالرسالة:\n$message\n";
$body .= "\n---\nتاريخ الإرسال: " . date('Y-m-d H:i') . "\n";

$fromName = '=?UTF-8?B?' . base64_encode('نموذج موقع ABT') . '?=';
$headers  = "From: $fromName <no-reply@abt-sa.com>\r\n";
if ($email !== '') {
    $headers .= "Reply-To: $email\r\n";
}
$headers .= "Content-Type: text/plain; charset=UTF-8\r\n";
$headers .= "X-Mailer: ABT-Contact-Form\r\n";

$sent = @mail($to, $subject, $body, $headers);

if ($sent) {
    echo json_encode(['success' => true]);
} else {
    http_response_code(500);
    echo json_encode(['success' => false, 'error' => 'mail_failed']);
}
