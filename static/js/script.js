document.addEventListener("DOMContentLoaded", function () {
    const dropbtn = document.querySelector("#menu-bar");
    const dropdownContent = document.querySelector("#navigation-panel");

    dropbtn.addEventListener("click", function (event) {
        event.preventDefault(); // Предотвращаем переход по ссылке

        // Добавляем/удаляем класс "show" для отображения меню
        dropdownContent.classList.toggle("show");

        // Останавливаем всплытие события, чтобы клик по кнопке не закрывал меню
        event.stopPropagation();
    });

    // Закрываем меню при клике вне него
    document.addEventListener("click", function (event) {
        if (!dropdownContent.contains(event.target) && !dropbtn.contains(event.target)) {
            dropdownContent.classList.remove("show");
        }
    });
});
