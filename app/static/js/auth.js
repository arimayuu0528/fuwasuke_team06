document.addEventListener('DOMContentLoaded', () => {
    const modal = document.getElementById('legal-modal');
    const title = document.getElementById('legal-title');
    const body = document.getElementById('legal-body');
    const closeBtn = document.getElementById('close-legal-modal');

    // 文章データ：バッククォート「 ` 」で囲むことで、改行したまま貼り付け可能です
    const legalTexts = {
        terms: `
            <section>
                <h2>第1条（規約の適用）</h2>
                <p>本規約は、習慣化サポートアプリ「ふわすけ」（以下、「本アプリ」）の利用に関し、ユーザーと運営者の間に適用されます。</p>

                <h2>第2条（サービスの提供内容）</h2>
                <p>本アプリは、ユーザーの気分登録、予定管理、およびタスク提案を通じて、ユーザーの生活習慣の定着を支援するサービスです。</p>

                <h2>第3条（アカウント管理）</h2>
                <p>ユーザーは、自身のログイン情報を自己の責任において管理するものとします。ログイン情報の管理不十分による損害の責任はユーザーが負うものとします。</p>

                <h2>第4条（禁止事項）</h2>
                <ul>
                    <li>法令または公序良俗に違反する行為</li>
                    <li>本アプリのサーバーやネットワーク機能を破壊・妨害する行為</li>
                    <li>他のユーザーへの迷惑行為</li>
                </ul>

                <h2>第5条（免責事項）</h2>
                <p>運営者は、本アプリの使用により生じた損害、および予定やタスクの履行不能について、一切の責任を負わないものとします。</p>
            </section>
        `,
        privacy: `
            <section>
                <h2>1. 収集する情報</h2>
                <p>本アプリでは、以下の情報を収集します。</p>
                <ul>
                    <li>アカウント情報（メールアドレス、パスワード）</li>
                    <li>生活データ（起床時間、就寝時間、気分、予定、タスク）</li>
                </ul>

                <h2>2. 利用目的</h2>
                <p>収集した情報は、以下の目的で利用します。</p>
                <ul>
                    <li>本人確認およびログイン機能の提供</li>
                    <li>ユーザーの気分や生活リズムに合わせたタスク提案</li>
                    <li>気分の変化をグラフで可視化する機能の提供</li>
                </ul>

                <h2>3. 情報の管理</h2>
                <p>ユーザーの同意なく個人情報を第三者に提供することはありません。また、本アプリを退会した際は、速やかにデータを削除いたします。</p>
            </section>
        `
    };

    // リンクをクリックしたときのイベント
    document.querySelectorAll('.legal-link').forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const type = e.target.dataset.type;
            title.textContent = type === 'terms' ? '利用規約' : 'プライバシーポリシー';
            body.innerHTML = legalTexts[type];
            modal.style.display = 'flex';
        });
    });

    if (closeBtn) {
        closeBtn.onclick = () => modal.style.display = 'none';
    }
    window.onclick = (e) => {
        if (e.target == modal) modal.style.display = 'none';
    };
});