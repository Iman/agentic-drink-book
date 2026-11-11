export const LANGUAGE_KEY = 'drinks-language';

export const translations = {
  en: {
    dir: 'ltr', title: 'Cocktail notebook', brand: 'Cocktail\nnotebook',
    home: 'Cocktail notebook home', language: 'Language', newChat: 'New conversation',
    startersLabel: 'Conversation starters', startersHeading: 'Something to start with',
    sidebarNote: 'From the first pour\nto the finished drink.',
    sidebarDetail: 'Recipes, fermentation & spirits.\nOne conversation at a time.',
    tagline: 'Drinks, and the craft of making them.', connecting: 'Connecting',
    disconnected: 'Disconnected', preparing: 'Preparing a reply', ready: 'Ready to chat',
    conversation: 'Conversation', welcome: 'What would you\nlike to make?',
    intro: 'A well-balanced cocktail. Your first batch of wine.\nThe story behind a Persian spirit. Start here.',
    quickCocktail: 'Mix a Negroni', quickWine: 'Make grape wine', messages: 'Messages', you: 'You',
    thinking: 'Preparing your reply. This can take a moment.', reconnect: 'Reconnect',
    question: 'Your drinks question', placeholder: 'Ask about a drink, an ingredient, a technique...',
    enterHint: 'to send', shiftHint: 'for a new line', pleaseWait: 'Please wait', send: 'Send',
    scope: 'Questions about drinks only. Answers can be mistaken; check food and equipment safety.',
    starters: [
      ['A balanced classic', 'How do I make a Negroni? Give me measurements and a method.'],
      ['Start with what you have', 'I have gin, lemons and honey. What cocktail can I make?'],
      ['Wine from scratch', 'Walk me through making grape wine from scratch, including sanitation and fermentation.'],
      ['Explore Persian spirits', 'What is Arak Sagi, and how is it traditionally made from raisins?'],
      ['Understand whiskey', 'Explain how whiskey is made from grain to aging, including equipment safety.'],
    ],
    errors: {
      connection: 'Could not connect. Check that the local server is running, then reconnect.',
      network: 'Connection lost. Your message is ready to retry.',
      generic: 'The request could not be completed. Please try again.',
      origin_denied: 'Request origin is not allowed.', invalid_language: 'Choose English or Persian.',
      session_expired: 'Your session expired. Reconnect to start a new conversation.',
      verification_failed: 'Request verification failed. Reconnect and try again.',
      session_capacity: 'Conversation capacity reached. Please try later.',
      session_busy: 'Wait for the current reply before resetting.', json_required: 'Send a JSON message.',
      body_too_large: 'Message is too large.',
      invalid_message: 'Send only a non-empty text message within the character limit.',
      busy: 'Too many requests or the service is busy. Please try again shortly.',
      unavailable: 'I cannot process this request right now. Please try again later.',
    },
  },
  fa: {
    dir: 'rtl', title: 'دفتر نوشیدنی', brand: 'دفتر\nنوشیدنی', home: 'صفحه اصلی دفتر نوشیدنی',
    language: 'زبان', newChat: 'گفت‌وگوی تازه', startersLabel: 'پیشنهادهای شروع گفت‌وگو',
    startersHeading: 'از اینجا شروع کنید', sidebarNote: 'از اولین جرعه\nتا نوشیدنی دلخواه شما.',
    sidebarDetail: 'دستور تهیه، تخمیر و نوشیدنی‌های تقطیری.\nهر بار، یک گفت‌وگو.',
    tagline: 'نوشیدنی‌ها و هنر تهیه آن‌ها.', connecting: 'در حال اتصال', disconnected: 'اتصال قطع است',
    preparing: 'در حال آماده کردن پاسخ', ready: 'آماده گفت‌وگو', conversation: 'گفت‌وگو',
    welcome: 'دوست دارید\nچه درست کنید؟',
    intro: 'یک کوکتل خوش‌طعم. اولین شراب دست‌ساز شما.\nداستان یک نوشیدنی ایرانی. از اینجا شروع کنید.',
    quickCocktail: 'تهیه نگرونی', quickWine: 'تهیه شراب انگور', messages: 'پیام‌ها', you: 'شما',
    thinking: 'پاسخ شما در حال آماده شدن است. ممکن است کمی طول بکشد.', reconnect: 'اتصال دوباره',
    question: 'پرسش شما درباره نوشیدنی‌ها', placeholder: 'درباره یک نوشیدنی، ماده اولیه یا روش تهیه بپرسید...',
    enterHint: 'برای ارسال', shiftHint: 'برای خط تازه', pleaseWait: 'کمی صبر کنید', send: 'ارسال',
    scope: 'فقط پرسش‌های مربوط به نوشیدنی‌ها. پاسخ‌ها ممکن است خطا داشته باشند؛ ایمنی مواد و تجهیزات را بررسی کنید.',
    starters: [
      ['یک کوکتل کلاسیک', 'نگرونی (Negroni) را چطور درست کنم؟ مقدار مواد و روش تهیه را بگو.'],
      ['با مواد موجود شروع کنید', 'جین، لیمو و عسل دارم. چه کوکتلی می‌توانم درست کنم؟'],
      ['شراب از ابتدا', 'روش تهیه شراب انگور از ابتدا، شامل بهداشت وسایل و تخمیر را توضیح بده.'],
      ['نوشیدنی‌های تقطیری ایرانی', 'عرق سگی چیست و به روش سنتی چطور از کشمش تهیه می‌شود؟'],
      ['آشنایی با ویسکی', 'روش تهیه ویسکی، از غلات تا کهنه‌سازی، همراه با ایمنی تجهیزات را توضیح بده.'],
    ],
    errors: {
      connection: 'اتصال برقرار نشد. از روشن بودن سرویس محلی مطمئن شوید و دوباره متصل شوید.',
      network: 'اتصال قطع شد. پیام شما برای ارسال دوباره آماده است.',
      generic: 'درخواست انجام نشد. لطفاً دوباره تلاش کنید.',
      origin_denied: 'مبدأ درخواست مجاز نیست.', invalid_language: 'زبان انگلیسی یا فارسی را انتخاب کنید.',
      session_expired: 'نشست شما منقضی شده است. برای گفت‌وگوی تازه دوباره متصل شوید.',
      verification_failed: 'درخواست تأیید نشد. دوباره متصل شوید و تلاش کنید.',
      session_capacity: 'ظرفیت گفت‌وگوها تکمیل شده است. لطفاً کمی بعد تلاش کنید.',
      session_busy: 'پیش از شروع گفت‌وگوی تازه، منتظر پایان پاسخ بمانید.',
      json_required: 'پیام را در قالب JSON ارسال کنید.', body_too_large: 'حجم پیام بیش از حد مجاز است.',
      invalid_message: 'فقط یک پیام متنی غیرخالی و در محدوده تعداد نویسه‌های مجاز ارسال کنید.',
      busy: 'تعداد درخواست‌ها زیاد است یا سرویس مشغول است. لطفاً کمی بعد تلاش کنید.',
      unavailable: 'اکنون امکان پاسخ‌گویی ندارم. لطفاً کمی بعد دوباره تلاش کنید.',
    },
  },
};

export function chooseLanguage(saved, browserLanguage = 'en') {
  if (saved === 'en' || saved === 'fa') return saved;
  return browserLanguage.toLowerCase().split('-')[0] === 'fa' ? 'fa' : 'en';
}

export function initialLanguage() {
  let saved;
  try { saved = localStorage.getItem(LANGUAGE_KEY); } catch { /* Storage can be disabled. */ }
  return chooseLanguage(saved, navigator.language);
}

export function applyLanguage(language) {
  document.documentElement.lang = language;
  document.documentElement.dir = translations[language].dir;
  document.title = translations[language].title;
  try { localStorage.setItem(LANGUAGE_KEY, language); } catch { /* Keep the in-memory preference. */ }
}
