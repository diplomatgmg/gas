## Есть 2 ветки для этого тз:  
### master
Делал в лоб по тз, без излишеств.  
Скорость выполнения get_transactions - ~3.7 sec (без цикла)  
Скорость выполнения get_transactions - ~38 sec (с циклом x10)  

### future
Как бы делал в реальных условиях.  
Использовал многопоточность для парсинга нескольких страниц транзакций подряд.  
Сделал код более поддерживаемым  
Скорость выполнения get_transactions - ~1.33 sec (без цикла)  
Скорость выполнения get_transactions - ~14 sec (с циклом x10)  
