// Fahamu Shamba Authentication JavaScript

const translations = {
    en: {
        title: "Farmer Login",
        rights: "All rights reserved.",
        login_title: "Welcome Back",
        login_subtitle: "Sign in to your farmer account",
        email_username: "Email or Username",
        email_username_placeholder: "Enter your email or username",
        password: "Password",
        password_placeholder: "Enter your password",
        remember_me: "Remember me",
        forgot_password: "Forgot password?",
        login_button: "Sign In",
        no_account: "Don't have an account?",
        register_link: "Sign up",
        register_title: "Create Account",
        register_subtitle: "Join our farming community",
        first_name: "First Name",
        first_name_placeholder: "Enter your first name",
        last_name: "Last Name",
        last_name_placeholder: "Enter your last name",
        email: "Email Address",
        email_placeholder: "Enter your email address",
        phone: "Phone Number",
        phone_placeholder: "Enter your phone number",
        confirm_password: "Confirm Password",
        confirm_password_placeholder: "Confirm your password",
        county: "County",
        select_county: "Select your county",
        agree_terms: "I agree to the",
        terms_link: "Terms & Conditions",
        newsletter: "Subscribe to newsletter",
        register_button: "Create Account",
        have_account: "Already have an account?",
        login_link: "Sign in",
        mobile_access: "Mobile Access",
        multilingual: "Multilingual Support",
        secure: "Secure & Private",
        password_weak: "Weak",
        password_medium: "Medium",
        password_strong: "Strong",
        required_field: "This field is required",
        invalid_email: "Please enter a valid email address",
        invalid_phone: "Please enter a valid phone number",
        password_too_short: "Password must be at least 8 characters",
        password_mismatch: "Passwords do not match",
        password_weak_error: "Password is too weak",
        terms_required: "You must agree to the terms and conditions",
        invalid_name: "Name can only contain letters and spaces"
    },
    sw: {
        title: "Kuingia kwa Mkulima",
        rights: "Haki zote zimehifadhiwa.",
        login_title: "Karibu Tena",
        login_subtitle: "Ingia kwenye akaunti yako ya mkulima",
        email_username: "Barua pepe au Jina la mtumiaji",
        email_username_placeholder: "Ingiza barua pepe au jina la mtumiaji",
        password: "Nenosiri",
        password_placeholder: "Ingiza nenosiri lako",
        remember_me: "Nikumbuke",
        forgot_password: "Umesahau nenosiri?",
        login_button: "Ingia",
        no_account: "Huna akaunti?",
        register_link: "Jisajili",
        register_title: "Tengeneza Akaunti",
        register_subtitle: "Jiunge na jumuiya yetu ya wakulima",
        first_name: "Jina la Kwanza",
        first_name_placeholder: "Ingiza jina lako la kwanza",
        last_name: "Jina la Mwisho",
        last_name_placeholder: "Ingiza jina lako la mwisho",
        email: "Anwani ya Barua Pepe",
        email_placeholder: "Ingiza anwani yako ya barua pepe",
        phone: "Nambari ya Simu",
        phone_placeholder: "Ingiza nambari yako ya simu",
        confirm_password: "Thibitisha Nenosiri",
        confirm_password_placeholder: "Thibitisha nenosiri lako",
        county: "Kaunti",
        select_county: "Chagua kaunti yako",
        agree_terms: "Ninakubali",
        terms_link: "Sheria na Masharti",
        newsletter: "Jisajili kwa jarida",
        register_button: "Tengeneza Akaunti",
        have_account: "Tayari una akaunti?",
        login_link: "Ingia",
        mobile_access: "Upatikanaji wa Simu",
        multilingual: "Msaada wa Lugha Nyingi",
        secure: "Salama na Faragha",
        password_weak: "Dhaifu",
        password_medium: "Wastani",
        password_strong: "Imara",
        required_field: "Uwanja huu unahitajika",
        invalid_email: "Tafadhali ingiza anwani ya barua pepe sahihi",
        invalid_phone: "Tafadhali ingiza nambari ya simu sahihi",
        password_too_short: "Nenosiri lazima liwe na angalau vibambo 8",
        password_mismatch: "Manenosiri hayafanani",
        password_weak_error: "Nenosiri ni dhaifu sana",
        terms_required: "Lazima ukubali sheria na masharti",
        invalid_name: "Jina linaweza kuwa na herufi na nafasi tu"
    },
    fr: {
        title: "Connexion Agriculteur",
        rights: "Tous droits reserves.",
        login_title: "Bienvenue",
        login_subtitle: "Connectez-vous a votre compte agriculteur",
        email_username: "Email ou Nom d'utilisateur",
        email_username_placeholder: "Entrez votre email ou nom d'utilisateur",
        password: "Mot de passe",
        password_placeholder: "Entrez votre mot de passe",
        remember_me: "Se souvenir de moi",
        forgot_password: "Mot de passe oublie?",
        login_button: "Se connecter",
        no_account: "Pas de compte?",
        register_link: "S'inscrire",
        register_title: "Creer un compte",
        register_subtitle: "Rejoignez notre communaute agricole",
        first_name: "Prenom",
        first_name_placeholder: "Entrez votre prenom",
        last_name: "Nom de famille",
        last_name_placeholder: "Entrez votre nom de famille",
        email: "Adresse email",
        email_placeholder: "Entrez votre adresse email",
        phone: "Numero de telephone",
        phone_placeholder: "Entrez votre numero de telephone",
        confirm_password: "Confirmer le mot de passe",
        confirm_password_placeholder: "Confirmez votre mot de passe",
        county: "Comte",
        select_county: "Selectionnez votre comte",
        agree_terms: "J'accepte les",
        terms_link: "Termes et Conditions",
        newsletter: "S'abonner a la newsletter",
        register_button: "Creer un compte",
        have_account: "Deja un compte?",
        login_link: "Se connecter",
        mobile_access: "Acces Mobile",
        multilingual: "Support Multilingue",
        secure: "Securise et Prive",
        password_weak: "Faible",
        password_medium: "Moyen",
        password_strong: "Fort",
        required_field: "Ce champ est requis",
        invalid_email: "Veuillez entrer une adresse email valide",
        invalid_phone: "Veuillez entrer un numero de telephone valide",
        password_too_short: "Le mot de passe doit contenir au moins 8 caracteres",
        password_mismatch: "Les mots de passe ne correspondent pas",
        password_weak_error: "Le mot de passe est trop faible",
        terms_required: "Vous devez accepter les termes et conditions",
        invalid_name: "Le nom ne peut contenir que des lettres et des espaces"
    }
};

let currentLang = localStorage.getItem("fahamu_lang") || "en";

function changeLanguage(lang) {
    if (!translations[lang]) {
        return;
    }
    currentLang = lang;
    localStorage.setItem("fahamu_lang", lang);
    updateFormLabels();
    document.title = translations[lang].title;
}

function updateFormLabels() {
    const lang = translations[currentLang];
    document.querySelectorAll("[data-translate]").forEach((element) => {
        const key = element.getAttribute("data-translate");
        if (!lang[key]) {
            return;
        }
        if (element.tagName === "INPUT" || element.tagName === "TEXTAREA") {
            element.placeholder = lang[key];
        } else {
            element.textContent = lang[key];
        }
    });

    document.querySelectorAll("[data-translate-option]").forEach((element) => {
        const key = element.getAttribute("data-translate-option");
        if (lang[key]) {
            element.textContent = lang[key];
        }
    });
}

function togglePassword(inputId) {
    const input = document.getElementById(inputId);
    if (!input) {
        return;
    }
    const toggleButton = input.parentElement ? input.parentElement.querySelector(".password-toggle i") : null;
    if (input.type === "password") {
        input.type = "text";
        if (toggleButton) {
            toggleButton.className = "fas fa-eye-slash";
        }
    } else {
        input.type = "password";
        if (toggleButton) {
            toggleButton.className = "fas fa-eye";
        }
    }
}

function updatePasswordStrength(password) {
    const strengthFill = document.getElementById("strength-fill");
    const strengthText = document.getElementById("strength-text");
    if (!strengthFill || !strengthText) {
        return;
    }

    if (!password) {
        strengthFill.className = "strength-fill";
        strengthFill.style.width = "0%";
        strengthText.textContent = "";
        return;
    }

    let score = 0;
    if (password.length >= 8) score++;
    if (password.length >= 12) score++;
    if (/[a-z]/.test(password)) score++;
    if (/[A-Z]/.test(password)) score++;
    if (/[0-9]/.test(password)) score++;
    if (/[^A-Za-z0-9]/.test(password)) score++;

    strengthFill.className = "strength-fill";
    strengthText.textContent = translations[currentLang].password_weak;

    if (score >= 6) {
        strengthFill.classList.add("strong");
        strengthText.textContent = translations[currentLang].password_strong;
    } else if (score >= 4) {
        strengthFill.classList.add("medium");
        strengthText.textContent = translations[currentLang].password_medium;
    } else {
        strengthFill.classList.add("weak");
        strengthText.textContent = translations[currentLang].password_weak;
    }
}

function showError(fieldId, message) {
    const errorElement = document.getElementById(`${fieldId}-error`);
    if (errorElement) {
        errorElement.textContent = message;
        errorElement.style.display = "flex";
    }

    const input = document.getElementById(fieldId);
    if (input) {
        input.style.borderColor = "var(--error-color)";
    }
}

function hideError(fieldId) {
    const errorElement = document.getElementById(`${fieldId}-error`);
    if (errorElement) {
        errorElement.textContent = "";
        errorElement.style.display = "none";
    }

    const input = document.getElementById(fieldId);
    if (input) {
        input.style.borderColor = "var(--border-color)";
    }
}

function validateEmail(email) {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

function validatePhone(phone) {
    return /^[+]?[1-9][\d]{0,15}$/.test(phone.replace(/[\s\-()]/g, ""));
}

function validateName(name) {
    return /^[a-zA-Z\s]+$/.test(name) && name.length >= 2;
}

function validateLoginForm() {
    let isValid = true;
    const identifierField = document.getElementById("identifier");
    const passwordField = document.getElementById("password");
    const identifier = identifierField ? identifierField.value.trim() : "";
    const password = passwordField ? passwordField.value : "";

    if (!identifier) {
        showError("identifier", translations[currentLang].required_field);
        isValid = false;
    } else {
        hideError("identifier");
    }

    if (!password) {
        showError("password", translations[currentLang].required_field);
        isValid = false;
    } else if (password.length < 8) {
        showError("password", translations[currentLang].password_too_short);
        isValid = false;
    } else {
        hideError("password");
    }

    return isValid;
}

function validateRegisterForm() {
    let isValid = true;
    const firstName = document.getElementById("first_name")?.value.trim() || "";
    const lastName = document.getElementById("last_name")?.value.trim() || "";
    const email = document.getElementById("email")?.value.trim() || "";
    const phone = document.getElementById("phone")?.value.trim() || "";
    const password = document.getElementById("password")?.value || "";
    const confirmPassword = document.getElementById("confirm_password")?.value || "";
    const county = document.getElementById("county")?.value || "";
    const terms = document.getElementById("terms")?.checked || false;

    if (!firstName) {
        showError("first_name", translations[currentLang].required_field);
        isValid = false;
    } else if (!validateName(firstName)) {
        showError("first_name", translations[currentLang].invalid_name);
        isValid = false;
    } else {
        hideError("first_name");
    }

    if (!lastName) {
        showError("last_name", translations[currentLang].required_field);
        isValid = false;
    } else if (!validateName(lastName)) {
        showError("last_name", translations[currentLang].invalid_name);
        isValid = false;
    } else {
        hideError("last_name");
    }

    if (!email) {
        showError("email", translations[currentLang].required_field);
        isValid = false;
    } else if (!validateEmail(email)) {
        showError("email", translations[currentLang].invalid_email);
        isValid = false;
    } else {
        hideError("email");
    }

    if (!phone) {
        showError("phone", translations[currentLang].required_field);
        isValid = false;
    } else if (!validatePhone(phone)) {
        showError("phone", translations[currentLang].invalid_phone);
        isValid = false;
    } else {
        hideError("phone");
    }

    if (!password) {
        showError("password", translations[currentLang].required_field);
        isValid = false;
    } else if (password.length < 8) {
        showError("password", translations[currentLang].password_too_short);
        isValid = false;
    } else {
        hideError("password");
    }

    if (!confirmPassword) {
        showError("confirm_password", translations[currentLang].required_field);
        isValid = false;
    } else if (password !== confirmPassword) {
        showError("confirm_password", translations[currentLang].password_mismatch);
        isValid = false;
    } else {
        hideError("confirm_password");
    }

    if (!county) {
        showError("county", translations[currentLang].required_field);
        isValid = false;
    } else {
        hideError("county");
    }

    if (!terms) {
        showError("terms", translations[currentLang].terms_required);
        isValid = false;
    } else {
        hideError("terms");
    }

    return isValid;
}

function checkPasswordMatch() {
    const password = document.getElementById("password")?.value || "";
    const confirmPassword = document.getElementById("confirm_password")?.value || "";
    if (confirmPassword && password !== confirmPassword) {
        showError("confirm_password", translations[currentLang].password_mismatch);
        return false;
    }
    hideError("confirm_password");
    return true;
}

document.addEventListener("DOMContentLoaded", () => {
    changeLanguage(currentLang);
});
