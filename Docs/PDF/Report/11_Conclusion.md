# 11. Заключение

## 11.1. Основные результаты исследования

Проведённый социологический анализ проблемы Skill Mismatch и Принципа Питера позволяет сделать следующие выводы:

1. **Skill Mismatch — системная, а не единичная проблема.** По данным ILO и OECD, от 25 до 45% работников находятся в состоянии несоответствия навыков требованиям должности. Это приводит к потерям производительности на уровне 7–10% ВВП для отдельных стран.

2. **Принцип Питера — не сатира, а эмпирически подтверждённый феномен.** Исследования на выборках в десятки тысяч сотрудников показывают, что повышение на основе текущей результативности систематически приводит к снижению эффективности на новой позиции.

3. **Традиционные методы оценки усугубляют проблему.** Межэкспертная надёжность оценок составляет лишь r = 0,45–0,52 (Salgado & Moscoso, 2019; Viswesvaran et al., 1996), идиосинкратический эффект оценщика объясняет 50–72% дисперсии (Scullen et al., 2000; Mount et al., 1998), а фактическая производительность — лишь 20–30% вариации оценок (Foster et al., 2024). Совокупные потери составляют $1 800–3 000 на сотрудника в год при устойчивом недоверии: 72% сотрудников не доверяют процессу оценки (Deloitte, 2025), 95% менеджеров выражают недовольство системой (PerformYard, 2026).

4. **ИИ-системы обеспечивают более быструю и воспроизводимую оценку.** Сокращение времени оценки составляет 25–58% (Nature, 2025; BCG, 2026); воспроизводимость ICC = 0,94–0,99 (Hackl et al., 2023); согласие с экспертами r = 0,90 (JMIR, 2026). Совокупное сокращение когнитивных искажений — 33% (Windmill, 2026). При этом 88% HR-лидеров не получили значимой бизнес-ценности при неструктурированном внедрении (Gartner, 2025), что обосновывает необходимость гибридной модели «ИИ + человек».

5. **Объективная оценка возможна через анализ рабочих артефактов.** Git-коммиты, метрики кода, данные code review содержат объективную информацию о реальном вкладе специалиста, доступную для автоматизированного анализа.

6. **Математическая модель с функцией затухания отражает динамику навыков.** Предложенная формула $P_{new} = P_{current} \times K + M$ с ролевыми коэффициентами позволяет моделировать накопление и устаревание компетенций, а также обнаруживать Принцип Питера по паттерну устойчивого снижения параметров после повышения.

7. **Сценарная матрица формул обеспечивает практическую диагностику.** Разработанный аппарат из 10 сценариев сопоставляет цель оценки, применимые формулы, нормативные пороги и сигналы Skill Mismatch для различных контекстов: от индивидуальной оценки (z-score, Efficiency) до отраслевых метрик (DORA, OEE, Sales Velocity).

## 11.2. Практическая значимость

Разработанная платформа DevMetrics демонстрирует, что:

- **Автоматизированное грейдирование** на основе 6 объективных параметров позволяет уйти от субъективности при оценке сотрудников
- **ИИ-анализ коммитов** обеспечивает непрерывный мониторинг вклада каждого члена команды
- **Система раннего предупреждения** позволяет выявлять Принцип Питера до того, как он нанесёт необратимый ущерб команде
- **Карьерные рекомендации** (promote/keep/demote) обеспечивают data-driven подход к управлению талантами

## 11.3. Социальная значимость

Решение проблемы Skill Mismatch имеет значение далеко за пределами отдельных организаций:

- **Справедливость оплаты труда** — компенсация начинает отражать реальный вклад, а не формальный статус
- **Социальная мобильность** — талантливые специалисты получают признание на основе заслуг, а не сигналов (диплом, связи)
- **Экономический рост** — оптимальное распределение человеческого капитала повышает совокупную производительность
- **Снижение профессионального выгорания** — люди работают на позициях, соответствующих их реальным навыкам

## 11.4. Перспективы развития

Дальнейшее развитие подхода предполагает:

1. **Расширение источников данных** — интеграция с Jira, Linear, SonarQube для более полного профиля компетенций
2. **Предиктивная аналитика** — прогнозирование успешности повышения на основе исторических данных команды
3. **Адаптация для других отраслей** — применение модели затухания к профессиям за пределами ИТ (наука, инженерия, медицина)
4. **Этические гарантии** — разработка механизмов прозрачности и обжалования автоматизированных решений

---

## Список использованных источников

1. Peter L.J., Hull R. *The Peter Principle: Why Things Always Go Wrong.* — New York: William Morrow & Co., 1969.

2. Benson A., Li D., Shue K. «Promotions and the Peter Principle» // *The Quarterly Journal of Economics.* — 2019. — Vol. 134, No. 4. — P. 2085–2134.

3. Strietska-Ilina O. «Skills and Jobs Mismatch: ILO Findings from Global Research» // International Labour Organization. — Geneva, 2017.

4. Stoevska V. «Qualification and Skill Mismatch: Concepts and Measurement» // ILO Department of Statistics. — Geneva, 2018.

5. Adalet McGowan M., Andrews D. «Labour Market Mismatch and Labour Productivity: Evidence from PIAAC Data» // OECD Economics Department Working Papers. — 2015. — No. 1209.

6. OECD. «Skills Mismatch, Productivity and Policies» // OECD Employment Outlook. — Paris, 2017.

7. Galeotti A., Merlino L. «Misallocation of Talent in Competitive Labor Markets» // IZA Discussion Paper. — 2014.

8. Hsieh C.-T., Hurst E., Jones C., Klenow P. «The Allocation of Talent and U.S. Economic Growth» // *Econometrica.* — 2019. — Vol. 87, No. 5. — P. 1439–1474.

9. Cavalcanti T., Guimaraes J., Pellegrina H. «Misallocation and Inequality» // IZA Discussion Paper No. 15174. — 2022.

10. Çelik M. «Does the Cream Always Rise to the Top? The Misallocation of Talent and Incentives in Corporate Research» // University of Toronto Working Paper. — 2018.

11. Cavaglia C., Etheridge B., Melolinna M. «Risk and the Misallocation of Human Capital» // Temple University Working Paper. — 2021.

12. Scullen S.E., Mount M.K., Goff M. «Understanding the Latent Structure of Job Performance Ratings» // *Journal of Applied Psychology.* — 2000. — Vol. 85, No. 6. — P. 956–970.

13. Viswesvaran C., Ones D.S., Schmidt F.L. «Comparative Analysis of the Reliability of Job Performance Ratings» // *Journal of Applied Psychology.* — 1996. — Vol. 81, No. 5. — P. 557–574.

14. Salgado J.F., Moscoso S. «The Validity of General Mental Ability for Five Performance Criteria: Hunter and Hunter (1984) Revisited» // *Frontiers in Psychology.* — 2019. — Vol. 10. — Art. 2227.

15. Arthur W.Jr., Bennett W.Jr., Stanush P.L., McNelly T.L. «Factors That Influence Skill Decay and Retention: A Quantitative Review and Analysis» // *Human Performance.* — 1998. — Vol. 11, No. 1. — P. 57–101.

16. Forsgren N., Humble J., Kim G. *Accelerate: The Science of Lean Software and DevOps.* — IT Revolution Press, 2018.

17. Grewe P. et al. «AI-Assisted Performance Evaluation: Comparing GPT-4 with Human Experts» // *Nature Scientific Reports.* — 2025. — Vol. 15.

18. Hackl V. et al. «GPT-4 as an Automated Essay Scoring Tool: Reliability and Validity» // *Frontiers in Education.* — 2023. — Vol. 8. — Art. 1260696.

\newpage
