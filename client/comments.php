<?php
$RAW = file_get_contents('php://input');
$METHOD = $_SERVER['REQUEST_METHOD'];

header('Content-Type: application/json; charset=utf-8');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: GET, POST, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type');
if ($METHOD === 'OPTIONS') { exit; }

$FILE = dirname(__FILE__) . '/comments.json';

function g($a, $k, $d) { return isset($a[$k]) ? $a[$k] : $d; }
function clip($s, $n) {
    $s = trim((string)$s);
    return function_exists('mb_substr') ? mb_substr($s, 0, $n, 'UTF-8') : substr($s, 0, $n);
}
function loadc($f) {
    $j = @file_get_contents($f);
    $d = json_decode($j, true);
    return is_array($d) ? $d : array();
}
function storec($f, $d) {
    $fp = @fopen($f, 'c+');
    if (!$fp) return false;
    flock($fp, LOCK_EX);
    ftruncate($fp, 0);
    rewind($fp);
    fwrite($fp, json_encode($d, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT));
    fflush($fp);
    flock($fp, LOCK_UN);
    fclose($fp);
    return true;
}
function newid() { return substr(md5(uniqid(mt_rand(), true)), 0, 12); }

if ($METHOD === 'GET') {
    echo json_encode(loadc($FILE), JSON_UNESCAPED_UNICODE);
    exit;
}

$in = json_decode($RAW, true);
if (!is_array($in)) {
    http_response_code(400);
    echo json_encode(array('error' => 'bad json', 'got' => substr($RAW, 0, 200)));
    exit;
}

$data = loadc($FILE);
$action = g($in, 'action', 'add');
$txt = clip(g($in, 'text', ''), 2000);
if ($txt === '') { http_response_code(400); echo '{"error":"empty text"}'; exit; }

if ($action === 'reply') {
    $id = g($in, 'id', '');
    foreach ($data as $i => $c) {
        if (g($c, 'id', '') === $id) {
            if (!isset($data[$i]['replies']) || !is_array($data[$i]['replies'])) {
                $data[$i]['replies'] = array();
            }
            $data[$i]['replies'][] = array(
                'text' => $txt, 'author' => 'gleb',
                'ts' => round(microtime(true) * 1000),
            );
        }
    }
} else {
    $data[] = array(
        'id'      => newid(),
        'page'    => preg_replace('/[^a-z0-9._-]/i', '', g($in, 'page', 'index.html')),
        'bi'      => intval(g($in, 'bi', -1)),
        'block'   => clip(g($in, 'block', ''), 120),
        'rx'      => max(0, min(1, floatval(g($in, 'rx', 0.5)))),
        'ry'      => max(0, min(1, floatval(g($in, 'ry', 0.5)))),
        'text'    => $txt,
        'author'  => 'client',
        'ts'      => round(microtime(true) * 1000),
        'replies' => array(),
    );
}

if (storec($FILE, $data)) echo '{"ok":true}';
else { http_response_code(500); echo '{"error":"save failed"}'; }
