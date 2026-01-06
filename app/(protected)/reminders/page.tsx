export default function RemindersPage() {
  return (
    <div>
      <h1 className="text-3xl font-bold mb-6">Hatırlatmalar</h1>

      <div className="space-y-4">
        <div className="bg-white p-4 rounded-xl shadow">
          🔔 Ahmet Yılmaz – Kasko bitiyor (3 gün kaldı)
        </div>
        <div className="bg-white p-4 rounded-xl shadow">
          🔔 Mehmet Kaya – DASK bitiyor (7 gün kaldı)
        </div>
      </div>
    </div>
  );
}
