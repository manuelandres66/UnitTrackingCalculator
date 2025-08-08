const getCSRFToken = () => {
  return document.querySelector('meta[name="csrf-token"]').getAttribute('content');
}; 

const now = document.getElementById("now");
const carry = document.getElementById("carry");
let isSecond = false;
let isFirstClick = true;
let system = 'MKS';
let ansValue = '';

let currentInput = "";
let carryInput = "";
let firstPart = ["", ""];
let secondPart = ["", ""];

const units = document.querySelectorAll(".unit");
const disableButtonsUnits = () => units.forEach(btn => btn.disabled = true);
const enableButtonsUnits = () => units.forEach(btn => btn.disabled = false);
disableButtonsUnits();

const numberButtons = document.querySelectorAll(".number");
const disableButtonsNumber = () => numberButtons.forEach(btn => btn.disabled = true);
const enableButtonsNumber = () => numberButtons.forEach(btn => btn.disabled = false);

const ansButton = document.getElementById('ans');
const disableAns = () => ansButton.disabled = true;
const enableAns = () => ansButton.disabled = false;

const operants = document.querySelectorAll(".operant");
const disableOperants = () => operants.forEach(btn => btn.disabled = true);
const enableOperants = () => operants.forEach(btn => btn.disabled = false);
disableOperants();

const unitChangers = document.querySelectorAll(".unitChanger");

const equalButton = document.getElementById('equal');
const disableEqual = () => equalButton.disabled = true;
const enableEqual = () => equalButton.disabled = false;
disableEqual();


const disableButRow = (type) => {
    disableButtonsUnits();
    document.querySelectorAll("." + type).forEach(btn => btn.disabled = false);
}

let currentType = "";
let currentOperant = "";

units.forEach(button => {
    button.addEventListener("click", () => {
        const value = button.getAttribute("data-value");
        currentInput += ' ' + value;
        now.value = currentInput;
        disableButtonsUnits();
        disableButtonsNumber();
        disableAns();
        enableOperants();
        if (isSecond) {
            disableOperants();
            enableEqual();
        } else {
            isSecond = true;
        }

        currentType = button.getAttribute('data-type');
});
});

operants.forEach(button => {
    button.addEventListener("click", () => {
        const value = button.getAttribute("data-value");
        firstPart = currentInput.split(" ");
        carryInput = currentInput + ' ' + value;
        carry.value = carryInput
        currentInput = '';
        now.value = '';
        enableButtonsNumber();
        enableAns();
        disableOperants();
        isFirstClick = true;
        currentOperant = value;
        isSecond = true;
    });
});

numberButtons.forEach(button => {
  button.addEventListener("click", () => {
    const value = button.getAttribute("data-value");
    currentInput += value;
    now.value = currentInput;
    disableAns();
    disableOperants();
    if (isFirstClick) {
        if (currentOperant == '+' || currentOperant == "-"){
            disableButRow(currentType);
        } else{
            enableButtonsUnits();
        }
        isFirstClick = false;
    };
  });
});

const ac = document.getElementById('ac');
ac.addEventListener('click', () => {
    enableAns();
    enableButtonsNumber();
    disableButtonsUnits();
    isFirstClick = true;
    isSecond = false;
    disableEqual();
    disableOperants();
    currentOperant = "";
    currentInput = "";
    carryInput = "";
    firstPart = ["", ""];
    secondPart = ["", ""];
    now.value = '';
    carry.value = '';
});


equalButton.addEventListener('click', () => {
    const secondPart = now.value.split(' ');


    fetch('/operation/', {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCSRFToken()
        },
        body: JSON.stringify({firstPart : firstPart, operant: currentOperant, secondPart: secondPart, system:system})
    }).then(response => {
        if (!response.ok) throw new Error('Network response was not ok');
        return response.json();
    }).then(data => {
        carry.value = "";
        if (!data.error) {
            now.value = data.result;
            currentInput = data.result;
            ansValue = data.result;
            firstPart = data.result.split(' ');
            enableOperants();
            disableEqual();
            isSecond = false;
            isFirstClick = true;
            const dataFinder = document.querySelector(`[data-value="${firstPart[1]}"]`);
            if (dataFinder != null) {currentType = dataFinder.getAttribute('data-type');} 
            else {
                currentType = '';
            };
        } else {
            disableAns();
            disableOperants();
            disableEqual();
            disableButtonsNumber();
            disableButtonsUnits();
            now.value = data.error;
        }
        
    })
});

const systemIndicators = document.querySelectorAll('.systemIndicator');
unitChangers.forEach(changer => {
    changer.addEventListener('click', () =>{
        system = changer.getAttribute('data-value');
        systemIndicators.forEach(indicator => {
            const value = indicator.getAttribute('data-value');
            if (value == system) {
                indicator.style.fontWeight = "bold";
            } else {
                indicator.style.fontWeight = 'normal';
            }
        });
    });
});

ansButton.addEventListener('click', () => {
    if (ansValue != '') {
        now.value = ansValue;
        currentInput = ansValue;
        if (isSecond) {
            secondPart = ansValue.split(' ');
            if (secondPart.length == 1) {secondPart = [secondPart[0], '']};
            disableOperants();
            disableAns();
            enableEqual();
        } else {
            firstPart = ansValue.split(' ');
            if (firstPart.length == 1) {firstPart = [firstPart[0], '']};
            enableOperants();
            enableAns();
        }
        disableButtonsNumber();
        disableButtonsUnits();
        isFirstClick = true;
        const dataFinder = document.querySelector(`[data-value="${ansValue.split(' ')[1]}"]`)
        if (dataFinder != null) {currentType = dataFinder.getAttribute('data-type');} else {
            currentType = '';
        }
        
    }
});

