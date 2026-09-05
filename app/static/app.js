const form = document.querySelector("#checkout-form");
const promptInput = document.querySelector("#prompt");
const sendButton = document.querySelector("#send-button");
const conversation = document.querySelector("#conversation");
const jsonOutput = document.querySelector("#json-output");
const guardrailBadge = document.querySelector("#guardrail-badge");
const outcome = document.querySelector("#outcome");

function addMessage(kind, label, text) {
  const message = document.createElement("div");
  message.className = `message ${kind}-message`;
  message.innerHTML = `<span class="message-label">${label}</span><p></p>`;
  message.querySelector("p").textContent = text;
  conversation.append(message);
  message.scrollIntoView({ behavior: "smooth", block: "nearest" });
}

function renderOutcome(response, httpOk) {
  const guardrail = response.guardrail_result;
  const isBlocked = guardrail && guardrail.passed === false;
  const isSuccess = response.success === true;
  const statusClass = isBlocked ? "blocked" : isSuccess ? "passed" : "error";
  const statusText = isBlocked ? "BLOCKED" : isSuccess ? "PASSED" : "ERROR";
  const detail = response.audit?.details || response.detail || "The checkout could not be completed.";

  guardrailBadge.className = `guardrail-badge ${statusClass}`;
  guardrailBadge.textContent = guardrail ? `Guardrail: ${statusText}` : statusText;
  outcome.className = `outcome-card ${statusClass}`;
  outcome.querySelector(".outcome-icon").textContent = isBlocked ? "!" : isSuccess ? "OK" : "x";
  outcome.querySelector("strong").textContent = isBlocked ? "Transaction blocked" : isSuccess ? "Order prepared" : "Checkout unavailable";
  outcome.querySelector("p").textContent = detail;

  if (isBlocked) {
    addMessage("agent", "NexusPay agent", `I found the item, but the guardrail stopped this transaction: ${detail}`);
  } else if (isSuccess) {
    const orderId = response.payment_order?.id;
    addMessage("agent", "NexusPay agent", orderId ? `Order ${orderId} is ready in test mode.` : "Your order passed the checks and is ready.");
  } else if (!httpOk) {
    addMessage("agent", "NexusPay agent", detail);
  }
}

async function submitCheckout(prompt) {
  addMessage("user", "You", prompt);
  sendButton.disabled = true;
  sendButton.querySelector("span").textContent = "Checking...";

  try {
    const response = await fetch("/api/v1/agentic-checkout", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ prompt }),
    });
    const data = await response.json();
    jsonOutput.textContent = JSON.stringify(data, null, 2);
    renderOutcome(data, response.ok);
  } catch (error) {
    const failure = { success: false, audit: { status: "FAILED", details: error.message } };
    jsonOutput.textContent = JSON.stringify(failure, null, 2);
    renderOutcome(failure, false);
  } finally {
    sendButton.disabled = false;
    sendButton.querySelector("span").textContent = "Send";
  }
}

form.addEventListener("submit", (event) => {
  event.preventDefault();
  const prompt = promptInput.value.trim();
  if (prompt) {
    promptInput.value = "";
    submitCheckout(prompt);
  }
});

document.querySelectorAll(".suggestion").forEach((button) => {
  button.addEventListener("click", () => {
    promptInput.value = button.dataset.prompt || "";
    promptInput.focus();
  });
});
