// static/js/scripts.js

// Loading Messages Array
const loadingMessages = [
  "Hold onto your bits, this might take a hot second... 🔥",
  "Teaching AI to read emails... it's like training a cat to swim 🐱",
  "Holy sh*t, this LLM is taking its sweet time... 🐌",
  "Parsing emails faster than your ex replies to texts... which isn't saying much 📱",
  "Making the hamsters run faster in our quantum computers... 🐹",
  "If this takes any longer, we might need to sacrifice a keyboard to the tech gods ⌨️",
  "Currently bribing the AI with virtual cookies 🍪",
  "Plot twist: The AI is actually your old Nokia trying its best 📱",
  "Damn, this is taking longer than explaining NFTs to your grandma 👵",
  "Our AI is having an existential crisis... again 🤖",
  "Loading... like your patience, probably 😅",
  "Working harder than a cat trying to bury poop on a marble floor 🐱",
  "Processing faster than your dating app matches ghost you 👻",
  "Better grab a coffee, this sh*t's taking its time ☕",
];

// Email Templates
const emailTemplates = {
  meeting: `Subject: Team Meeting - Project Update
From: manager@company.com
To: team@company.com
Date: March 15, 2024

Hi team,

Let's meet to discuss the project progress. The meeting is scheduled for March 20, 2024 at 2:00 PM EST in Conference Room A.

Agenda:
1. Project timeline review
2. Resource allocation
3. Next steps

Please confirm your attendance.

Best regards,
Manager`,
  invoice: `Subject: Invoice #INV-2024-001
From: billing@supplier.com
To: accounts@company.com
Date: March 16, 2024

Dear Customer,

Please find attached invoice #INV-2024-001 for recent services.

Amount Due: $1,500.00
Due Date: March 30, 2024

Payment Details:
Bank: FirstBank
Account: 1234567890
Reference: INV-2024-001

Thank you for your business!

Regards,
Billing Team`,
  shipping: `Subject: Your Order Has Shipped!
From: orders@store.com
To: customer@email.com
Date: March 17, 2024

Dear Customer,

Your order #ORD123456 has shipped!

Tracking Number: 1Z999AA1234567890
Carrier: UPS
Estimated Delivery: March 20, 2024

Order Details:
- Product A ($99.99)
- Product B ($149.99)

Track your package here: https://tracking.ups.com

Thank you for shopping with us!

Best regards,
Store Team`,
};

let currentTheme = "light";
let currentMessageIndex = 0;
let loadingInterval;
let progressValue = 0;

// Global array to store parsed entries
let parsedEntries = [];

// Initialize Lottie Animations
let loadingAnimation;
document.addEventListener("DOMContentLoaded", () => {
  const lottieContainer = document.getElementById("lottie-container");
  if (lottieContainer) {
    loadingAnimation = lottie.loadAnimation({
      container: lottieContainer,
      renderer: "svg",
      loop: true,
      autoplay: false,
      path: "https://lottie.host/0c1a139c-8469-489f-a94e-d6f8e379b066/8eOki65eVz.json", // Update with your loading animation URL
    });
  }

  const successAnimationContainer = document.getElementById("success-animation");
  if (successAnimationContainer) {
    // Initialize success animation if needed
  }
});

// Theme Toggle Function
function toggleTheme() {
  currentTheme = currentTheme === "light" ? "dark" : "light";
  document.documentElement.setAttribute("data-theme", currentTheme);
  localStorage.setItem("theme", currentTheme);
  updateThemeIcon();
}

function updateThemeIcon() {
  const themeIcon = document.getElementById("theme-icon");
  if (themeIcon) {
    themeIcon.textContent = currentTheme === "light" ? "🌙" : "☀️";
  }
}

// Load Email Template into Textarea
function loadTemplate() {
  const selector = document.getElementById("template_selector");
  const textarea = document.getElementById("email_content");
  if (selector && textarea) {
    textarea.value = emailTemplates[selector.value] || "";
    updateCharCount();
  }
}

// Update Character Count
function updateCharCount() {
  const textarea = document.getElementById("email_content");
  const charCount = document.getElementById("char_count");
  if (textarea && charCount) {
    charCount.textContent = `${textarea.value.length} characters`;
  }
}

// Show Loading Overlay
function showLoadingOverlay() {
  const overlay = document.querySelector(".loading-overlay");
  const messageElement = document.getElementById("loading-message");
  const progressBar = document.getElementById("progress-bar");

  if (overlay && messageElement && progressBar) {
    overlay.classList.remove("d-none");
    loadingAnimation.play();

    progressValue = 0;
    progressBar.style.width = "0%";

    updateLoadingMessage();

    loadingInterval = setInterval(() => {
      currentMessageIndex = (currentMessageIndex + 1) % loadingMessages.length;
      updateLoadingMessage();

      progressValue = Math.min(progressValue + 2, 90);
      progressBar.style.width = `${progressValue}%`;
    }, 3000);
  }
}

// Hide Loading Overlay
function hideLoadingOverlay() {
  const overlay = document.querySelector(".loading-overlay");
  const progressBar = document.getElementById("progress-bar");

  if (overlay && progressBar) {
    progressBar.style.width = "100%";

    setTimeout(() => {
      overlay.classList.add("d-none");
      loadingAnimation.stop();
      clearInterval(loadingInterval);
      currentMessageIndex = 0;
    }, 500);
  }
}

// Update Loading Message
function updateLoadingMessage() {
  const messageElement = document.getElementById("loading-message");
  if (messageElement) {
    messageElement.classList.remove("visible");

    setTimeout(() => {
      messageElement.textContent = loadingMessages[currentMessageIndex];
      messageElement.classList.add("visible");
    }, 300);
  }
}

// Copy Parsed Results to Clipboard
function copyResults() {
  const resultsCode = document.getElementById("jsonOutput");
  if (resultsCode) {
    navigator.clipboard
      .writeText(resultsCode.textContent)
      .then(() => {
        showSuccessMessage("Parsed data copied to clipboard!");
      })
      .catch(() => {
        showErrorMessage("Failed to copy to clipboard.");
      });
  }
}

// Show Success Message
function showSuccessMessage(message) {
  const successDiv = document.getElementById("successMessage");
  if (successDiv) {
    successDiv.textContent = message;
    successDiv.classList.remove("d-none");
    setTimeout(() => {
      successDiv.classList.add("d-none");
    }, 5000);
  }
}

// Show Error Message
function showErrorMessage(message) {
  const errorDiv = document.getElementById("errorMessage");
  if (errorDiv) {
    errorDiv.textContent = message;
    errorDiv.classList.remove("d-none");
    setTimeout(() => {
      errorDiv.classList.add("d-none");
    }, 5000);
  }
}

// Download CSV Function
function downloadCSV() {
  if (parsedEntries.length === 0) {
    showErrorMessage("No parsed data available to download.");
    return;
  }

  // Extract headers from the first entry
  const headers = Object.keys(parsedEntries[0]);

  // Create CSV content
  const csvContent = [
    headers.join(","), // Header row
    ...parsedEntries.map(entry =>
      headers.map(header => {
        let cell = entry[header];
        if (typeof cell === "object" && cell !== null) {
          cell = JSON.stringify(cell);
        }
        // Escape double quotes by replacing " with ""
        cell = String(cell).replace(/"/g, '""');
        // If the cell contains a comma, newline, or double quote, wrap it in double quotes
        if (/[",\n]/.test(cell)) {
          cell = `"${cell}"`;
        }
        return cell;
      }).join(",")
    ),
  ].join("\n");

  // Create a Blob from the CSV content
  const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);

  // Create a temporary link to trigger the download
  const link = document.createElement("a");
  link.setAttribute("href", url);
  const timestamp = new Date().toISOString().replace(/[:\-T.]/g, "").split("Z")[0];
  link.setAttribute("download", `parsed_emails_${timestamp}.csv`);
  link.style.visibility = "hidden";
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);

  showSuccessMessage("CSV downloaded successfully!");
}

// Display Parsed Data in the UI and Accumulate for CSV
function displayParsedData(parsedData) {
  const outputDiv = document.getElementById("jsonOutput");
  if (outputDiv) {
    const prettyJson = JSON.stringify(parsedData, null, 2);
    outputDiv.textContent = prettyJson;
    Prism.highlightElement(outputDiv);
  }

  // Accumulate parsed data for CSV
  // Flatten nested objects if necessary
  const flattenedData = flattenParsedData(parsedData);
  parsedEntries.push(flattenedData);

  // Show Download CSV button
  const downloadBtn = document.getElementById("downloadCsvBtn");
  if (downloadBtn) {
    downloadBtn.classList.remove("d-none");
  }
}

// Flatten parsed data to ensure each QuickBase field is a top-level key
function flattenParsedData(data) {
  const flatData = {};

  // Iterate through each section
  for (const [section, content] of Object.entries(data)) {
    if (typeof content === "object" && content !== null) {
      for (const [key, value] of Object.entries(content)) {
        flatData[`${section} - ${key}`] = value;
      }
    } else {
      flatData[section] = content;
    }
  }

  return flatData;
}

// Handle Form Submission
function handleFormSubmission() {
  const parserForm = document.getElementById("parserForm");
  if (parserForm) {
    parserForm.addEventListener("submit", function (e) {
      e.preventDefault();
      console.log("Form submission intercepted.");
      const formData = new FormData(this);
      const parserOption = document.getElementById("parser_option").value;
      const emailContent = document.getElementById("email_content").value.trim();

      // Client-side Validation
      if (!emailContent) {
        const textarea = document.getElementById("email_content");
        if (textarea) {
          textarea.classList.add("is-invalid");
        }
        console.log("Email content is empty.");
        showErrorMessage("Please enter the email content to parse.");
        return;
      } else {
        const textarea = document.getElementById("email_content");
        if (textarea) {
          textarea.classList.remove("is-invalid");
        }
      }

      // Show Loading Overlay
      showLoadingOverlay();

      fetch("/parse_email", {
        method: "POST",
        body: formData,
      })
        .then(async (response) => {
          hideLoadingOverlay();
          const contentType = response.headers.get("Content-Type");
          if (contentType && contentType.includes("application/json")) {
            const data = await response.json();
            if (!response.ok) {
              throw new Error(
                data.error_message || "An error occurred while parsing."
              );
            }
            return data;
          } else {
            throw new Error("Unexpected response format.");
          }
        })
        .then((data) => {
          console.log("Parsed data received:", data);
          if (data.error_message) {
            showErrorMessage(data.error_message);
            const outputDiv = document.getElementById("jsonOutput");
            if (outputDiv) {
              outputDiv.textContent = "";
            }
            const downloadBtn = document.getElementById("downloadCsvBtn");
            if (downloadBtn) {
              downloadBtn.classList.add("d-none");
            }
          } else {
            displayParsedData(data);
            showSuccessMessage("Email parsed successfully!");
          }
        })
        .catch((error) => {
          console.error("Error during parsing:", error);
          hideLoadingOverlay();
          showErrorMessage(error.message);
          const downloadBtn = document.getElementById("downloadCsvBtn");
          if (downloadBtn) {
            downloadBtn.classList.add("d-none");
          }
        });
    });
  }
}

// Initialize Event Listeners
document.addEventListener("DOMContentLoaded", () => {
  // Initialize Theme
  const savedTheme = localStorage.getItem("theme") || "light";
  document.documentElement.setAttribute("data-theme", savedTheme);
  currentTheme = savedTheme;
  updateThemeIcon();
  console.log(`Theme initialized to: ${currentTheme}`);

  // Initialize Character Count
  const textarea = document.getElementById("email_content");
  if (textarea) {
    textarea.addEventListener("input", updateCharCount);
    console.log("Character count listener attached.");
  }

  // Handle Form Submission
  handleFormSubmission();
  console.log("Form submission listener attached.");

  // Handle Template Selector Change
  const templateSelector = document.getElementById("template_selector");
  if (templateSelector) {
    templateSelector.addEventListener("change", loadTemplate);
    console.log("Template selector change listener attached.");
  } else {
    console.error("Template selector with id 'template_selector' not found.");
  }
});
