import asyncio
import logging
from aiogram.types import Message
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.builtin import Command

from datetime import datetime
from keyboards.default.back import back
from keyboards.default.main_menu import main_button
from loader import db, dp



@dp.message_handler(text="✅Test topshirish")
async def precheck_answers(message: Message, state: FSMContext):
    await message.answer("Iltimos Testga qatnashishdan oldin hozirda faol bo'lgan raqamingizni kiriting \
bu siz bilan bog'lanish uchun. Agar raqam kiritmasangiz testga qatnasha olmaysiz \
\nMasalan: 991234567", reply_markup=back)
    await state.set_state("phone_num")



@dp.message_handler(state="phone_num")
async def check_test_number(message: Message, state: FSMContext):
    num = message.text
    if len(num)==9:
        await db.update_user_phone(int(num), telegram_id=message.from_user.id)
        
        await message.answer("Test raqamini yuboring, \n\n bekor qilish uchun esa ortga tugmasidan foydaling", reply_markup=back)
        await state.set_state("test_number")
    else:
        await message.answer("Iltimos raqamni yana bir tekshirib ko'ring", reply_markup=back)



@dp.message_handler(state="test_number")
async def check_test_number(message: Message, state: FSMContext):
    
    number = message.text
    if number.isdigit():
        number = int(message.text)
        if await db.check_config_participation(message.from_user.id, test_number=number):
            await message.answer("Siz oldin bu testda qatnashgansiz siz bitta testga bir\
marta qatnasha olasiz boshqa testlarga qatnashishga harakat qilib ko'ring", reply_markup=back)
        else:
                
            current_test_number = await db.select_inserted_test_number()
            if number>current_test_number:
                await message.answer(f"{number}- raqamli test mavjud emas qayta urib ko'ring")
            else:
                test_data = await db.select_test_all_data(test_number=number)
                start = test_data["start_date"]
                end = test_data["end_date"]
                print("bu yerga keldi1")
                if start and end:
                    
                    start = datetime(int(start[6:10]), int(start[3:5]), int(start[:2]), int(start[11:13]), int(start[14:16]))
                    end = datetime(int(end[6:10]), int(end[3:5]), int(end[:2]), int(end[11:13]), int(end[14:16]))
                    now = datetime.now()
                    if start > now:
                        print(start > now)
                        await message.answer("Bu test hali boshlanmagan birozdan so'ng urunib ko'ring", reply_markup=back)
                    else:
                        if end > now:
                            print(end, now)
                            await message.answer("endi javoblarni yuboring \n Masalan : 1a2b3c4d5a6b\n E'tiborli bo'ling sizda faqatgina bitta javob yuborish imkoni bor", reply_markup=back)
                            await state.set_state("check_answers")
                            await state.update_data({
                                "test_number" : number
                            })
                        else:
                            await message.answer("Afsus bu test allaqachon tugagan 😔 \nbosh menuga qaytish uchun /start  bosing", reply_markup=back)
                            await state.finish()
                elif start and not end:
                    now = datetime.now()
                    start = datetime(int(start[6:10]), int(start[3:5]), int(start[:2]), int(start[11:13]), int(start[14:16]))
                    if start>now:
                        await message.answer("Bu test hali boshlanmagan birozdan so'ng urunib ko'ring", reply_markup=back)
                    else:
                        await state.set_state("check_answers")
                        await state.update_data({
                                    "test_number" : number
                                })
                        await message.answer("endi javoblarni yuboring \n Masalan : 1a2b3c4d5a6b\n E'tiborli \
bo'ling sizda faqatgina bitta javob yuborish imkoni bor!", reply_markup=back)
                elif end and not start:
                    end = datetime(int(end[6:10]), int(end[3:5]), int(end[:2]), int(end[11:13]), int(end[14:16]))
                    now = datetime.now()
                    if end > now:
                        await state.set_state("check_answers")
                        await state.update_data({                   
                   
                   
                                    "test_number" : number
                                })
                        await message.answer("endi javoblarni yuboring \n Masalan : abcdabcds\n E'tiborli \
bo'ling sizda faqatgina bitta javob yuborish imkoni bor!", reply_markup=back)
                    else:
                        await message.answer("Afsus bu test allaqachon tugagan 😔 \nbosh menuga qaytish uchun /start  bosing", reply_markup=back)
                        await state.finish()
                else:  # ikkalasiyam skip bo'lsa 
                    await state.set_state("check_answers")
                    await state.update_data({                                      
                                    "test_number" : number
                                })
                    await message.answer("endi javoblarni yuboring \n Masalan : abcdabcds\n E'tiborli \
bo'ling sizda faqatgina bitta javob yuborish imkoni bor!", reply_markup=back)

    else:
        await message.answer("Iltimos faqat sonlardan foydalaning", reply_markup=back)
                        


        


@dp.message_handler(state="check_answers")
async def check_answers(message: Message, state: FSMContext):
    user_answer = message.text.lower()
    data = await state.get_data()

    answers = await db.select_test_all_data(test_number=data["test_number"])
    
    true_answers = answers['answers']

    list1_user = []
    list2_true = []

    togri_javob = 0
    notogri_javob = 0

    if len(user_answer) == len(true_answers):
            
        for i in range(1, len(user_answer), 2):
            list1_user.append(user_answer[i].lower())

        for y in range(1, len(true_answers), 2):
            list2_true.append(true_answers[y].lower())

        for test1 in range(len(list2_true)):
            if list2_true[test1] == list1_user[test1]:
                togri_javob += 1
            else:
                notogri_javob += 1



        await message.answer(f"Javoblaringiz qabul qilindi \nto'g'ri javoblar soni: {togri_javob}\nreyting \
natijalarini test yakunlangandan keyin olasiz sog' bo'ling!", reply_markup=main_button)
        await db.insert_test_config(int(data["test_number"]), message.from_user.id, user_answer, int(togri_javob), datetime.now())
        await state.finish()

    else:
        await message.answer(f"Siz yuborgan javoblar soni {int(len(user_answer)/2)} umumiy test savollari soniga teng emas \
\nbilmagan savollarinizni tahminiy harflar bilan belgilang!", reply_markup=back)
# bazaga kiritamiz 
    



#=====================================================================================================


dp.message_handler(text="/start")
async def participated_tests(message:Message):
    # logging.info(message)
    # datas = await db.participated_tests(user_id=message.from_user.id)
    # logging.info(datas)
    my_tests = "Siz qatnashgan testlar bo'yicha jami ma'lumot"
    counter = 0
    # for data in datas:
    #     my_tests+=f" {data[0]}"
    #     my_tests+=f"Test raqami: {data[1]}\n"
    #     my_tests+=f"Javoblar: {data[2]}\n"
    #     my_tests+=f"Natija: {data[3]}\n"
    #     my_tests+=f"Topshirilgan : {data[4]}\n"
    #     counter +=1
    my_tests +=f"<b>Barcha qatnashilgan testlar soni</b>: {counter}"
    await message.answer(my_tests, reply_markup=main_button)