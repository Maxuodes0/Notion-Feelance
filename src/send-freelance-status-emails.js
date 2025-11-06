// send-freelance-status-emails.js

require('dotenv').config();
const { Client } = require('@notionhq/client');
const nodemailer = require('nodemailer');

// --------------------------------------
// إعداد Notion
// --------------------------------------
// نستخدم نفس NOTION_TOKEN و NOTION_DB_ID اللي عندك
const notion = new Client({ auth: process.env.NOTION_TOKEN });
const FREELANCE_DB_ID = process.env.NOTION_DB_ID;

if (!process.env.NOTION_TOKEN || !FREELANCE_DB_ID) {
  console.error('❌ تأكد من ضبط NOTION_TOKEN و NOTION_DB_ID في المتغيرات البيئية');
  process.exit(1);
}

// --------------------------------------
// إعداد البريد (Gmail)
// --------------------------------------
const transporter = nodemailer.createTransport({
  service: 'gmail',
  auth: {
    user: process.env.MAIL_USER,
    pass: process.env.MAIL_PASS, // بدون مسافات في السيكريت
  },
});

async function sendEmail({ to, subject, text }) {
  const from = process.env.MAIL_FROM || process.env.MAIL_USER;

  try {
    await transporter.sendMail({ from, to, subject, text });
    console.log(`📧 تم إرسال إيميل إلى: ${to}`);
    return true;
  } catch (err) {
    console.error(`❌ فشل الإرسال إلى ${to}:`, err.message);
    return false;
  }
}

// --------------------------------------
// دوال قراءة الخصائص من Notion (لداتابيسك الحالية)
// --------------------------------------
function getStatus(page) {
  const prop = page.properties['حالة الطلب'];
  if (!prop) return '';
  if (prop.type === 'select' && prop.select) return prop.select.name || '';
  if (prop.type === 'status' && prop.status) return prop.status.name || '';
  return '';
}

function getEmail(page) {
  const prop = page.properties['البريد الإلكتروني'];
  if (!prop || prop.type !== 'email') return '';
  return prop.email || '';
}

function getName(page) {
  const prop = page.properties['الاسم'];
  if (!prop || prop.type !== 'title') return '';
  return (prop.title || []).map(t => t.plain_text).join(' ').trim();
}

function getEmailFlag(page) {
  const prop = page.properties['تم ارسال ايميل؟'];
  if (!prop || prop.type !== 'rich_text') return '';
  return (prop.rich_text || []).map(t => t.plain_text).join(' ').trim();
}

async function setEmailFlag(pageId, text) {
  await notion.pages.update({
    page_id: pageId,
    properties: {
      'تم ارسال ايميل؟': {
        rich_text: [
          {
            type: 'text',
            text: {
              content: text || 'تم الإرسال',
            },
          },
        ],
      },
    },
  });
}

// (اختياري) لو حاب تستخدم اسم المشروع داخل نص الإيميل
function getProjectName(page) {
  const prop =
    page.properties['اسم المشروع المقدم عليه'] ||
    page.properties['المشروع المقدم عليه '] ||
    page.properties['المشروع المقدم عليه'];
  if (!prop) return '';
  if (prop.type === 'rich_text') {
    return (prop.rich_text || []).map(t => t.plain_text).join(' ').trim();
  }
  if (prop.type === 'title') {
    return (prop.title || []).map(t => t.plain_text).join(' ').trim();
  }
  if (prop.type === 'select' && prop.select) {
    return prop.select.name || '';
  }
  return '';
}

// --------------------------------------
// نصوص الإيميل حسب حالة الطلب (للفريلانسر)
// عدّل الكلام هنا زي ما يناسبك
// --------------------------------------
function getEmailContent(status, name, projectName) {
  let subject, text;

  const projectPart = projectName ? ` على مشروع "${projectName}"` : '';

  switch (status) {
    case 'قيد الانتظار':
      subject = 'تم استلام طلبك';
      text =
`مرحباً ${name}،

تم استلام طلبك${projectPart}، وحالته الآن "قيد الانتظار".
سيتم مراجعة طلبك والتواصل معك بالتحديثات في أقرب وقت.

مع التحية،`;
      break;

    case 'مقبول':
    case 'موافقة':
      subject = 'تم قبول طلبك';
      text =
`مرحباً ${name}،

يسعدنا إبلاغك بأنه تم قبول طلبك${projectPart} ✅
سيتم التنسيق معك بخصوص الخطوات القادمة وتفاصيل التنفيذ.

مع تمنياتنا لك بالتوفيق،`;
      break;

    case 'مرفوض':
    case 'مرفوضة':
      subject = 'تحديث بخصوص طلبك';
      text =
`مرحباً ${name}،

نود إبلاغك بأنه لم يتم قبول طلبك${projectPart} في الوقت الحالي.
يمكنك التقديم على فرص أخرى مستقبلاً، ونتمنى لك كل التوفيق.

مع التحية،`;
      break;

    default:
      subject = 'تحديث حالة طلبك';
      text =
`مرحباً ${name}،

تم تحديث حالة طلبك${projectPart} إلى: "${status}".

مع التحية،`;
  }

  return { subject, text };
}

// --------------------------------------
// قراءة جميع الطلبات من قاعدة Notion
// --------------------------------------
async function fetchAllRequests() {
  const results = [];
  let cursor;

  do {
    const response = await notion.databases.query({
      database_id: FREELANCE_DB_ID,
      start_cursor: cursor,
      page_size: 100,
    });

    results.push(...response.results);
    cursor = response.has_more ? response.next_cursor : null;
  } while (cursor);

  return results;
}

// --------------------------------------
// الوظيفة الرئيسية
// --------------------------------------
async function run() {
  console.log('🚀 بدء فحص الطلبات لإرسال الإيميلات...\n');

  const requests = await fetchAllRequests();
  let sent = 0;
  let skipped = 0;

  for (const page of requests) {
    const status = getStatus(page);
    const email = getEmail(page);
    const name = getName(page);
    const flag = getEmailFlag(page);
    const projectName = getProjectName(page);

    console.log('------------------------------');
    console.log(`🔎 طلب: ${name || '(بدون اسم)'}`);
    console.log(`   حالة الطلب       : "${status || 'فاضي'}"`);
    console.log(`   البريد الإلكتروني : "${email || 'فاضي'}"`);
    console.log(`   المشروع           : "${projectName || 'فاضي'}"`);
    console.log(`   تم ارسال ايميل؟   : "${flag || 'فاضي'}"`);

    // 1) لا يوجد حالة
    if (!status) {
      console.log('⏭️ تم التجاوز: حالة الطلب فاضية');
      skipped++;
      continue;
    }

    // 2) لا يوجد ايميل
    if (!email) {
      console.log('⏭️ تم التجاوز: البريد الإلكتروني فاضي');
      skipped++;
      continue;
    }

    // 3) سبق إرسال إيميل لنفس هذه الحالة (نخزن الحالة في حقل "تم ارسال ايميل؟")
    if (flag && flag.trim() === status.trim()) {
      console.log('⏭️ تم التجاوز: سبق إرسال إيميل لنفس هذه الحالة');
      skipped++;
      continue;
    }

    // 4) إرسال الإيميل
    const { subject, text } = getEmailContent(status, name, projectName);

    console.log(`📨 محاولة إرسال إيميل إلى: ${email} (حالة: ${status})`);
    const ok = await sendEmail({ to: email, subject, text });

    if (ok) {
      await setEmailFlag(page.id, status);
      console.log('✅ تم الإرسال وتحديث حقل "تم ارسال ايميل؟"');
      sent++;
    } else {
      console.log('❌ فشل الإرسال لهذا الطلب');
      skipped++;
    }
  }

  console.log('\n📊 ملخص الإرسال:');
  console.log(`✅ تم الإرسال: ${sent}`);
  console.log(`⏭️ تم التجاوز: ${skipped}`);
  console.log('✨ انتهى الإرسال.');
}

// --------------------------------------
// تشغيل مباشر من السطر
// --------------------------------------
if (require.main === module) {
  run()
    .then(() => process.exit(0))
    .catch((err) => {
      console.error('❌ خطأ أثناء التنفيذ:', err);
      process.exit(1);
    });
}

module.exports = { run };
